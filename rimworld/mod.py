import logging
import re
from typing import Collection, Iterator, Self, cast
from dataclasses import dataclass
from pathlib import Path
from bisect import bisect_left
from lxml import etree

from .xml import load_xml
from .gameversion import GameVersion


# Regular expressions to match version strings
VERSION_RE = re.compile(r'\d+(\.\d+)+')
V_VERSION_RE = re.compile(r'v(\d+(\.\d+)+)')



@dataclass
class ModAbout:
    """
    Represents metadata about a mod.

    Attributes:
        package_id (str): The package ID of the mod.
        author (str | None): The author of the mod.
        supported_versions (list[str]): List of supported versions.
    """

    package_id: str  # package ID of the mod
    author: str|None  # author of the mod
    name: str|None  # name of the mod
    supported_versions: list[str]  # list of supported versions

    @classmethod
    def load(
            cls, 
            filepath: Path  # path to xml file
            ) -> Self:
        """ Load the mod metadata from an XML file """
        
        xml = load_xml(filepath)
        package_id_element = xml.find('packageId')
        author_element = xml.find('author')
        name_element = xml.find('name')

        assert isinstance(package_id_element, etree._Element) and package_id_element.text
        author = author_element.text if isinstance(author_element, etree._Element) else None
        
        supported_versions = xml.xpath('/ModMetaData/supportedVersions/li/text()')
        assert isinstance(supported_versions, list)

        name = name_element.text if isinstance(name_element, etree._Element) else None

        return cls(
                package_id_element.text, 
                author, 
                name,
                cast(list[str], supported_versions),
                )



@dataclass(frozen=True)
class Mod:
    """
    Represents a mod and provides methods to load and manage mod folders.

    """

    about: ModAbout  # Mod metadata
    path: Path  # Filesystem path to the mod

    @property
    def package_id(self) -> str:
        """ Lowercase package ID of the mod """        
        return self.about.package_id.lower()

    @classmethod
    def load(
            cls, 
            path: Path  # filesystem path to the mod
            ) -> Self:
        """ Load a mod from the given path """

        logging.getLogger(__name__).info(f'Loading mod at {path}')
        about_path = path.joinpath('About').joinpath('About.xml')
        about = ModAbout.load(about_path)
        return cls(about, path)

    def get_mod_folders(
            self, 
            game_version: GameVersion|None, # The game version; use latest available version if None
            loaded_mods: Collection[str]|None=None  # List of loaded mod ids
            ) -> list[Path]:
        """ Return a list of mod folders based on the game version and loaded mods """
        
        if self.path.joinpath('LoadFolders.xml').is_file():
            return self._get_mod_folders_loadfolders(game_version, loaded_mods)
        return self._get_mod_folders_default(game_version)
        
    def _get_mod_folders_default(
            self, 
            game_version: GameVersion|None  # The game version; use latest available version if None
            ) -> list[Path]:
        """ Return a list of default mod folders based on the game version """

        result = [self.path]

        if (common:=self.path.joinpath('Common')).is_dir():
            result.append(common)
        
        listed_versions = [GameVersion.from_string(d.name) for d in self.path.iterdir() if d.is_dir() and VERSION_RE.match(d.name)]
        if (version_:= _get_matching_version(listed_versions, game_version)) is not None:
            result.append(self.path.joinpath(str(version_)))
    
        return result

    def _get_mod_folders_loadfolders(
            self, game_version: GameVersion|None,  # The game version; use latest available version if None
            loaded_mods: Collection[str]|None=None  #  List of loaded mod ids
            ) -> list[Path]:
        """ Return a list of mod folders based on LoadFolders.xml """        

        listed_versions = []
        loaded_mods = loaded_mods or []

        loadfolders_filepath = self.path.joinpath('LoadFolders.xml')
        xml = load_xml(loadfolders_filepath)

        structure = {}

        for elt in xml.getroot():
            v_version_re_match = V_VERSION_RE.match(elt.tag)
            if not v_version_re_match:
                raise RuntimeError(f'Unknown item in ListFolders.xml: {elt.tag}')
            v_version = GameVersion.from_string(v_version_re_match.group(1))
            listed_versions.append(v_version)

            structure[v_version] = []

            for li in elt.findall('li'):
                modactive = li.get('IfModActive')
                if (not modactive) or modactive in loaded_mods:
                    text = li.text or ''
                    structure[v_version].append('' if text.strip()=='/' else text)

        matching_version = _get_matching_version(listed_versions, game_version)

        if matching_version is None:
            return []

        return [self.path.joinpath(x) for x in structure[matching_version]]

    def get_def_files(self) -> Iterator[Path]:
        pass


def _get_matching_version(versions: list[GameVersion], version: GameVersion|None) -> GameVersion|None:
    """ Find the closest matching version from a list of versions """
    versions = list(sorted(versions))
    if version is None:
        return max(versions) if versions else None
    return (
            version
            if version in versions else 
            versions[x-1] if (x:=bisect_left(versions, version)) else None
            )
