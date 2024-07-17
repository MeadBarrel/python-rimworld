"""
Module for modeling RimWorld's mod metadata formats.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Collection, Iterable, Iterator, Self, Sequence, cast

from lxml import etree

from .gameversion import GameVersion
from .xml import (XMLSerializable, deserialize_from_list,
                  deserialize_strings_from_list, element_text_or_none,
                  ensure_element_text, find_xmls, load_xml, make_element,
                  serialize_as_list, serialize_strings_as_list)

__all__ = [
    "Mod",
    "ModDependency",
    "ModAbout",
    "ModsConfig",
    "LoadFolders",
    "NotAModFolderError",
    "is_mod_folder",
    "load_mods",
    "select_mods",
]


class NotAModFolderError(Exception):
    """Raised when trying to load a mod from a folder that is not a mod folder"""


class _ModFolder(Path):

    @property
    def defs_folder(self) -> Path:
        """Defs folder"""
        return self.joinpath("Defs")

    @property
    def patches_folder(self) -> Path:
        """Patches folder"""
        return self.joinpath("Patches")

    @property
    def textures_folder(self) -> Path:
        """Textures folder"""
        return self.joinpath("Textures")

    @property
    def sounds_folder(self) -> Path:
        """Sounds folder"""
        return self.joinpath("Sounds")

    @property
    def assemblies_folder(self) -> Path:
        """Assemblies folder"""
        return self.joinpath("Assemblies")

    @property
    def languages_folder(self) -> Path:
        """Languages folder"""
        return self.joinpath("Languages")


class AbsoluteModFolder(_ModFolder):
    """Represents a single mod folder with absolute path"""

    def def_files(self) -> Iterator[Path]:
        """Yields paths for all the def files in this folder"""
        yield from find_xmls(self.defs_folder)

    def patch_files(self) -> Iterator[Path]:
        """Yields paths for all the patch files in this folder"""
        yield from find_xmls(self.patches_folder)


class RelativeModFolder(_ModFolder):
    """Represents a single mod folder, relative to the mod's root folder"""

    def with_root(self, root: Path) -> AbsoluteModFolder:
        """Prepends a root folder to this folder"""
        return AbsoluteModFolder(root.joinpath(self))


@dataclass(frozen=True)
class LoadFolder:
    """Models a record in LoadFolders.xml"""

    path: Path
    if_mod_active: str | None

    def should_include(self, active_package_ids: Collection[str]) -> bool:
        """Check if the load folder should be included when loading a mod"""
        if self.if_mod_active is None:
            return True
        return self.if_mod_active in active_package_ids


@dataclass(frozen=True)
class ModDependency(XMLSerializable):
    """Describes a mod dependency"""

    package_id: str
    display_name: str | None = None
    steam_workshop_url: str | None = None

    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        """
        Deserialize a ModDependency from an XML node.

        Args:
            node (etree._Element): The XML node to deserialize.


        Returns:

            ModDependency: The deserialized ModDependency object.

        Example xml node:
            ```xml
              <packageId>brrainz.harmony</packageId>
              <displayName>Harmony</displayName>
              <steamWorkshopUrl>steam://url/CommunityFilePage/2009463077</steamWorkshopUrl>

            ```
        """
        return cls(
            ensure_element_text(node.find("packageId")),
            element_text_or_none(node.find("displayName")),
            element_text_or_none(node.find("steamWorkshopUrl")),
        )

    def to_xml(self, parent: etree._Element):
        """
        Serialize the ModDependency into an XML node.


        Args:
            node (etree._Element): The XML node to append the serialized data to.
        """

        parent.append(make_element("packageId", self.package_id))
        if self.display_name:
            parent.append(make_element("displayName", self.display_name))
        if self.steam_workshop_url:
            parent.append(make_element("steamWorkshopUrl", self.steam_workshop_url))


@dataclass(frozen=True)
class ModAbout:
    """
    Represents metadata about a mod.

    Attributes:
        package_id (str): The package ID of the mod.
        authors (list[str]): The authors of the mod.
        name (str): The name of the mod.
        description (str): The description of the mod.
        supported_versions (tuple[GameVersion]): The game versions supported by the mod.
        mod_version (str | None): The version of the mod.
        mod_icon_path (str | None): The path to the mod's icon.
        url (str | None): The URL for the mod.
        descriptions_by_version (dict[GameVersion, str] | None): Descriptions by game version.
        mod_dependencies (list[ModDependency]): The list of mod dependencies.
    """

    package_id: str
    authors: list[str]
    supported_versions: tuple[GameVersion] | None = None
    name: str | None = None
    mod_version: str | None = None
    mod_icon_path: str | None = None
    url: str | None = None
    description: str | None = None
    descriptions_by_version: dict[GameVersion, str] | None = None
    steam_app_id: str | None = None
    mod_dependencies: list[ModDependency] = field(default_factory=list)
    mod_dependencies_by_version: dict[GameVersion, list[ModDependency]] = field(
        default_factory=dict
    )
    load_before: list[str] = field(default_factory=list)
    load_before_by_version: dict[GameVersion, list[str]] = field(default_factory=dict)

    force_load_before: list[str] = field(default_factory=list)
    load_after: list[str] = field(default_factory=list)
    load_after_by_version: dict[GameVersion, list[str]] = field(default_factory=dict)
    force_load_after: list[str] = field(default_factory=list)
    incompatible_with: list[str] = field(default_factory=list)
    incompatible_with_by_version: dict[GameVersion, list[str]] = field(
        default_factory=dict
    )

    def __post_init__(self):
        if not self.authors:
            raise RuntimeError("Should have at least one author")

    @classmethod
    def load(cls, filepath: Path) -> Self:  # path to xml file
        """
        Load the mod metadata from an XML file.


        Args:
            filepath (Path): The path to the XML file.

        Returns:
            ModAbout: The deserialized ModAbout object.
        """

        xml = load_xml(filepath)
        return cls.from_xml(xml)

    def save(self, path: Path):
        """Save to LoadFolders.xml file"""
        xml = self.to_xml()
        xml.write(path, encoding="utf-8", pretty_print=True, xml_declaration=True)

    def to_xml(self) -> etree._ElementTree:
        """
        Serialize the mod metadata into XML format.

        Returns:
            etree._ElementTree: The serialized XML tree.
        """

        root = etree.Element("ModMetaData")
        result = etree.ElementTree(root)

        root.append(make_element("packageId", self.package_id))
        if self.description:
            root.append(make_element("description", self.description))
        if self.name:
            root.append(make_element("name", self.name))
        self._serialize_authors(root)
        self._serialize_supported_versions(root)

        if self.mod_version:
            root.append(make_element("modVersion", self.mod_version))
        if self.mod_icon_path:
            root.append(make_element("modIconPath", self.mod_icon_path))
        if self.url:
            root.append(make_element("url", self.url))

        self._serialize_descriptions_by_version(root)

        if self.steam_app_id:
            root.append(make_element("steamAppId", self.steam_app_id))

        if self.mod_dependencies:
            serialize_as_list(
                make_element("modDependencies", parent=root), self.mod_dependencies
            )

        if self.mod_dependencies_by_version:
            self._serialize_mod_dependencies_by_version(
                make_element("modDependenciesByVersion", parent=root),
                self.mod_dependencies_by_version,
            )

        if self.load_before:
            serialize_strings_as_list(
                make_element("loadBefore", parent=root), self.load_before
            )

        if self.load_after_by_version:
            self._serialize_gameversion_dict_strings(
                make_element("loadBeforeByVersion", parent=root),
                self.load_before_by_version,
            )

        if self.force_load_before:
            serialize_strings_as_list(
                make_element("forceLoadBefore", parent=root), self.force_load_before
            )

        if self.load_after:
            serialize_strings_as_list(
                make_element("loadAfter", parent=root), self.load_after
            )

        if self.load_after_by_version:
            self._serialize_gameversion_dict_strings(
                make_element("loadAfterByVersion", parent=root),
                self.load_after_by_version,
            )

        if self.force_load_after:
            serialize_strings_as_list(
                make_element("forceLoadAfter", parent=root), self.force_load_after
            )

        if self.incompatible_with:
            serialize_strings_as_list(
                make_element("incompatibleWith", parent=root), self.incompatible_with
            )

        if self.incompatible_with_by_version:
            self._serialize_gameversion_dict_strings(
                make_element("incompatibleWithByVersion", parent=root),
                self.incompatible_with_by_version,
            )

        return result

    @classmethod
    def from_xml(cls, xml: etree._ElementTree) -> Self:
        """
        Deserialize the mod metadata from XML format.

        Args:
            xml (etree._ElementTree): The XML tree to deserialize.

        Returns:
            ModAbout: The deserialized ModAbout object.
        """

        mod_dependencies = []
        if node := xml.find("modDependencies"):
            mod_dependencies = deserialize_from_list(node, ModDependency)

        mod_dependencies_by_version = {}
        if node := xml.find("modDependenciesByVersion"):
            mod_dependencies_by_version = cls._deserialize_mod_dependencies_by_version(
                node
            )

        load_before = []
        if node := xml.find("loadBefore"):
            load_before = deserialize_strings_from_list(node)

        load_before_by_version = {}
        if node := xml.find("loadBeforeByVersion"):
            load_before_by_version = cls._deserialize_gameversion_dict_strings(node)

        force_load_before = []
        if (node := xml.find("forceLoadBefore")) is not None:
            force_load_before = deserialize_strings_from_list(node)

        load_after = []
        if (node := xml.find("loadAfter")) is not None:
            load_after = deserialize_strings_from_list(node)

        load_after_by_version = {}
        if node := xml.find("loadAfterByVersion"):
            load_after_by_version = cls._deserialize_gameversion_dict_strings(node)

        force_load_after = []
        if (node := xml.find("forceLoadAfter")) is not None:
            force_load_after = deserialize_strings_from_list(node)

        incompatible_with = []
        if node := xml.find("incompatibleWith"):
            incompatible_with = deserialize_strings_from_list(node)

        incompatible_with_by_version = {}
        if node := xml.find("incompatibleWithByVersion"):
            incompatible_with_by_version = cls._deserialize_gameversion_dict_strings(
                node
            )

        return cls(
            package_id=ensure_element_text(xml.find("packageId")),
            authors=cls._deserialize_authors(xml),
            name=element_text_or_none(xml.find("name")),
            description=element_text_or_none(xml.find("description")),
            supported_versions=cls._deserialize_supported_versions(xml),
            mod_version=element_text_or_none(xml.find("modVersion")),
            mod_icon_path=element_text_or_none(xml.find("modIconPath")),
            url=element_text_or_none(xml.find("url")),
            descriptions_by_version=cls._deserialize_descriptions_by_version(xml),
            steam_app_id=element_text_or_none(xml.find("steamAppId")),
            mod_dependencies=mod_dependencies,
            mod_dependencies_by_version=mod_dependencies_by_version,
            load_before=load_before,
            load_before_by_version=load_before_by_version,
            force_load_before=force_load_before,
            load_after=load_after,
            load_after_by_version=load_after_by_version,
            force_load_after=force_load_after,
            incompatible_with=incompatible_with,
            incompatible_with_by_version=incompatible_with_by_version,
        )

    # Serialization
    def _serialize_authors(self, root: etree._Element):
        assert self.authors
        if len(self.authors) == 1:
            root.append(make_element("author", self.authors[0]))
        elif len(self.authors) > 1:
            root.append(
                make_element(
                    "authors",
                    children=[make_element("li", author) for author in self.authors],
                )
            )

    def _serialize_supported_versions(self, root: etree._Element):
        if self.supported_versions is None:
            return
        root.append(
            make_element(
                "supportedVersions",
                children=[
                    make_element("li", str(version))
                    for version in self.supported_versions
                ],
            )
        )

    def _serialize_descriptions_by_version(self, root: etree._Element):
        if not self.descriptions_by_version:
            return
        node = make_element(
            "descriptionsByVersion",
            children=[
                make_element(f"v{str(k)}", v)
                for k, v in self.descriptions_by_version.items()
            ],
        )
        root.append(node)

    @staticmethod
    def _serialize_mod_dependencies_by_version(
        parent: etree._Element, dict_: dict[GameVersion, list[ModDependency]]
    ):
        for k, v in dict_.items():
            version_elt = make_element(f"v{k}", parent=parent)
            for v_ in v:
                elt = make_element("li", parent=version_elt)
                v_.to_xml(elt)

    @staticmethod
    def _serialize_gameversion_dict_strings(
        parent: etree._Element, dict_: dict[GameVersion, list[str]]
    ):
        for k, v in dict_.items():
            version_elt = make_element(f"v{k}", parent=parent)
            for v_ in v:
                make_element("li", v_, parent=version_elt)

    # Deserialization
    @staticmethod
    def _deserialize_authors(xml: etree._ElementTree) -> list[str]:
        # authors
        authors = []
        if (authors_elt := xml.find("authors")) is not None:
            for node in authors_elt.findall("li"):
                authors.append(ensure_element_text(node))
        if author := element_text_or_none(xml.find("author")):
            authors.append(author)

        if not authors:
            raise RuntimeError("Must have at least one author")
        return authors

    @staticmethod
    def _deserialize_supported_versions(
        xml: etree._ElementTree,
    ) -> tuple[GameVersion] | None:
        supported_versions_raw = xml.xpath("/ModMetaData/supportedVersions/li/text()")
        if not supported_versions_raw:
            return None
        assert isinstance(supported_versions_raw, list)
        supported_versions_raw = cast(list[str], supported_versions_raw)
        supported_versions_raw = [x.strip() for x in supported_versions_raw]
        supported_versions = tuple(map(GameVersion.new, supported_versions_raw))
        return supported_versions

    @staticmethod
    def _deserialize_descriptions_by_version(
        xml: etree._ElementTree,
    ) -> dict[GameVersion, str] | None:
        result = {}
        node = xml.find("descriptionsByVersion")
        if node is None:
            return None
        for child in node:
            version = GameVersion.match(child.tag)
            if version is None:
                continue
            if child.text is None:
                raise RuntimeError("Description missing")
            result[version] = child.text
        return result

    @staticmethod
    def _deserialize_gameversion_dict_strings(
        parent: etree._Element,
    ) -> dict[GameVersion, list[str]]:
        result: dict[GameVersion, list[str]] = {}
        for node in parent:
            version = GameVersion.match(node.tag)
            if version is None:
                continue
            result[version] = [ensure_element_text(li) for li in node.findall("li")]
        return result

    @staticmethod
    def _deserialize_mod_dependencies_by_version(
        parent: etree._Element,
    ) -> dict[GameVersion, list[ModDependency]]:
        result: dict[GameVersion, list[ModDependency]] = {}
        for node in parent:
            version = GameVersion.match(node.tag)
            if version is None:
                continue
            result[version] = [ModDependency.from_xml(li) for li in node.findall("li")]
        return result


class LoadFolders:
    """Models LoadFolders.xml"""

    load_folders: dict[GameVersion, list[LoadFolder]]

    def __init__(
        self, load_folders: dict[GameVersion, Sequence[str | Path | LoadFolder]]
    ) -> None:
        self._load_folders = {}
        for version, folders in load_folders.items():
            folders_for_this_version = []
            for item in folders:
                match item:
                    case str():
                        if item.startswith("/"):
                            item = f".{item}"
                        load_folder = LoadFolder(Path(item), None)
                    case Path():
                        load_folder = LoadFolder(item, None)
                    case LoadFolder():
                        load_folder = item
                folders_for_this_version.append(load_folder)

            self._load_folders[version] = folders_for_this_version

    def all_folders(self):
        """Return paths to all listed mod folders"""
        for folders in self._load_folders.values():
            for folder in folders:
                yield RelativeModFolder(folder.path)

    def compatible_folders(
        self, game_version: GameVersion, active_package_ids: Collection[str]
    ) -> Iterator[RelativeModFolder]:
        """Return paths to mod folders for this game version and active mods

        Return None if there are no records compatible with `game_version`
        """
        matching_version = game_version.get_matching_version(self._load_folders.keys())
        if matching_version is None:
            return
        for folder in self._load_folders[matching_version]:
            if folder.should_include(active_package_ids):
                yield RelativeModFolder(folder.path)

    @classmethod
    def load(cls, path: Path) -> Self:
        """Load from LoadFolders.xml file"""
        xml = load_xml(path)
        return cls.from_xml(xml)

    def save(self, path: Path):
        """Save to LoadFolders.xml file"""
        xml = self.to_xml()
        xml.write(path, encoding="utf-8", pretty_print=True, xml_declaration=True)

    @classmethod
    def from_xml(cls, xml: etree._ElementTree) -> Self:
        """Deserialize from xml"""
        result = {}
        root = xml.getroot()
        if root.tag.lower() != "loadfolders":
            raise RuntimeError(
                f"Cannot parse loadFolders: incoorect root tag ({root.tag})"
            )
        for version_node in root:
            version = GameVersion.match(version_node.tag)
            if version is None:
                continue
            this_version_folders = []
            for li in version_node.findall("li"):
                if_mod_active = li.get("IfModActive")
                path = element_text_or_none(li) or ""
                if path.startswith("/"):
                    path = f".{path}"
                this_version_folders.append(LoadFolder(Path(path), if_mod_active))
            this_version_folders.reverse()
            result[version] = this_version_folders
        return cls(result)

    def to_xml(self) -> etree._ElementTree:
        """Serialize into an xml"""
        root = etree.Element("loadFolders")
        result = etree.ElementTree(root)
        for version, folders in self._load_folders.items():
            version_element = etree.Element(f"v{version}")
            root.append(version_element)
            for folder in reversed(folders):
                li = etree.Element("li")
                if folder.if_mod_active is not None:
                    li.set("IfModActive", folder.if_mod_active)
                path = folder.path.as_posix()
                if path == ".":
                    path = "/"
                version_element.append(li)
        return result


@dataclass(frozen=True)
class Mod:
    """
    Represents a mod and provides methods to load and manage mod folders.

    """

    path: Path
    about: ModAbout
    loadfolders: LoadFolders | None

    @property
    def package_id(self) -> str:
        """Lowercase package ID of the mod"""
        return self.about.package_id.lower()

    @classmethod
    def load(cls, path: Path) -> Self:
        """Load a mod from the given path"""
        logging.getLogger(__name__).info("Loading mod at %s", path)

        about_path = path.joinpath("About", "About.xml")
        if not about_path.exists():
            raise NotAModFolderError(path)
        about = ModAbout.load(about_path)

        loadfolders_path = path.joinpath("LoadFolders.xml")
        loadfolders = None
        if loadfolders_path.exists():
            loadfolders = LoadFolders.load(loadfolders_path)

        return cls(path, about=about, loadfolders=loadfolders)

    def mod_folders(self, mods_config: "ModsConfig") -> Iterator[AbsoluteModFolder]:
        """Return a list of mod folders based on the game version and loaded mods"""

        if self.loadfolders is not None:
            yield from (
                f.with_root(self.path)
                for f in self.loadfolders.compatible_folders(
                    mods_config.version, mods_config.active_mods
                )
            )
        else:
            yield RelativeModFolder().with_root(self.path)
            yield RelativeModFolder("Common").with_root(self.path)
            matching_version = mods_config.version.get_matching_version(
                self.about.supported_versions or []
            )
            if matching_version is not None:
                yield RelativeModFolder(str(matching_version)).with_root(self.path)

    def _default_folders(self) -> Iterator[RelativeModFolder]:
        """Return default mod folders for this mod"""
        yield RelativeModFolder()
        yield RelativeModFolder("Common")
        for version in self.about.supported_versions or []:
            yield RelativeModFolder(str(version))

    def def_files(self, mods_config: "ModsConfig") -> Iterator[Path]:
        """Iterate through absolute paths to all .xml files in Defs"""
        for mod_folder in self.mod_folders(mods_config):
            yield from mod_folder.def_files()

    def patch_files(self, mods_config: "ModsConfig") -> Iterator[Path]:
        """Iterate through absolute paths to all .xml files in Patches"""
        for mod_folder in self.mod_folders(mods_config):
            yield from mod_folder.patch_files()


@dataclass(frozen=True)
class ModsConfig:
    """Model for ModsConfig.xml"""

    version: GameVersion
    active_mods: list[str]
    known_expansions: list[str]

    @classmethod
    def load(cls, path: Path) -> Self:
        """Load from an .xml file"""
        xml = load_xml(path)
        return cls.from_xml(xml)

    @classmethod
    def from_xml(cls, xml: etree._ElementTree) -> Self:
        """Load from xml"""

        active_mods_elt = xml.find("activeMods")
        if active_mods_elt is None:
            raise RuntimeError("Element must be present: activeMods")

        known_expansions_elt = xml.find("knownExpansions")
        if known_expansions_elt is None:
            raise RuntimeError("Element must be present: knownExpansions")

        return cls(
            version=GameVersion.new(ensure_element_text(xml.find("version"))),
            active_mods=deserialize_strings_from_list(active_mods_elt),
            known_expansions=deserialize_strings_from_list(known_expansions_elt),
        )

    def to_xml(self) -> etree._ElementTree:
        """Serialize as xml"""
        root = etree.Element("ModsConfigData")
        result = etree.ElementTree(root)
        root.append(make_element("version", str(self.version)))
        serialize_strings_as_list(
            make_element("activeMods", parent=root), self.active_mods
        )
        serialize_strings_as_list(
            make_element("knownExpansions", parent=root), self.known_expansions
        )
        return result


def is_mod_folder(path: Path) -> bool:
    """Check if a folder is a mod folder"""
    if not path.is_dir():
        return False
    return path.joinpath("About", "About.xml").exists()


def load_mods(*folders: Path) -> Iterator[Mod]:
    """Recursively load mods from folders"""
    for folder in folders:
        if not folder.is_dir():
            continue
        if is_mod_folder(folder):
            yield Mod.load(folder)
            continue
        for sf in folder.iterdir():
            yield from load_mods(sf)


def select_mods(
    mods: Iterable[Mod],
    package_id_in: Collection[str] | None = None,
    name_in: Collection[str] | None = None,
) -> Iterator[Mod]:
    """Filter out mods"""

    for mod in mods:
        if package_id_in is not None and mod.package_id not in package_id_in:
            continue
        if name_in is not None and mod.about.name not in name_in:
            continue
        yield mod
