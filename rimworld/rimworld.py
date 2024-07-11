from dataclasses import dataclass, field
from functools import cached_property
import logging
from pathlib import Path
from typing import Collection, NamedTuple, cast

from lxml import etree

from .mod import GameVersion, Mod
from .xml import empty_defs, load_xml, find_xmls, merge



@dataclass
class Rimworld:
    mods: list[Mod] = field(default_factory=list)
    version: GameVersion|None = None

    @cached_property
    def active_package_ids(self) -> set[str]:
        return {mod.package_id for mod in self.mods}

    @cached_property
    def active_package_names(self) -> set[str]:
        return {mod.about.name for mod in self.mods if mod.about.name}



class _Modlist(NamedTuple):
    active_package_ids: list[str]
    known_expansions: list[str]


def load_xml_data(mods: Collection[Mod], game_version: GameVersion|None=None) -> etree._ElementTree:
    loaded_package_ids = [mod.package_id for mod in mods]
    result = empty_defs()
    total_added = 0
    for mod in mods:
        logging.getLogger().info(f'Loading and merging mod {mod}')
        for path in mod.get_mod_folders(game_version, loaded_package_ids):
            defs_folder = path.joinpath('Defs')
            if not defs_folder.is_dir():
                continue
            for xml_path in find_xmls(defs_folder):
                logging.getLogger(__name__).info(f'Loading and merging {str(xml_path)}')
                added = merge(result, load_xml(xml_path))
                total_added += added
                logging.getLogger(__name__).info(f'{added} defs added')
    logging.getLogger(__name__).info(f'Total {total_added} defs added')
    return result


def load_mods(path: Path|Collection[Path]) -> list[Mod]:
    if isinstance(path, Path):
        if not path.is_dir():
            return []
        if is_mod_folder(path):
            return [Mod.load(path)]
        return load_mods(list(path.iterdir()))
    
    result = []
    for p in path:
        result.extend(load_mods(p))

    return result


def read_modlist(filepath: Path) -> _Modlist:
    """
    Read and parse the modlist XML file.


    Args:
        filepath (Path): The path to the modlist XML file.

    Returns:
        _Modlist: A _Modlist instance containing active mod package IDs and known expansions.

    Raises:
        AssertionError: If the parsed XML does not contain expected elements.
    """    
    xml = load_xml(filepath)

    mods = xml.xpath('/ModsConfigData/activeMods/*/text()')
    assert isinstance(mods, list)
    assert all(isinstance(x, str) for x in mods)

    known_expansions = xml.xpath('/ModsConfigData/knownExpansions/*/text()')
    assert isinstance(known_expansions, list)
    assert all(isinstance(x, str) for x in known_expansions)

    return _Modlist(cast(list[str], mods), cast(list[str], known_expansions))


def is_mod_folder(path: Path) -> bool:
    p = path.joinpath('About', 'About.xml')
    return p.exists() and p.is_file()
