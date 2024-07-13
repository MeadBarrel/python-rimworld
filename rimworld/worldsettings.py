from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Self, Sequence, cast
from rimworld.gameversion import GameVersion

from rimworld.mod import Mod
from rimworld.settings import Settings, create_settings
from rimworld.xml import load_xml


@dataclass(frozen=True)
class WorldSettings:
    mods: tuple[Mod]
    version: GameVersion

    @classmethod
    def from_settings(cls, settings: Settings|None=None) -> Self:
        settings = settings or create_settings()
        all_mods = load_mod_infos(settings.mod_folders)
        active_package_ids, _ = read_modlist(settings.rimworld_modlist_filename)
        mods = [m for m in all_mods if m.package_id in active_package_ids]
        version = GameVersion.from_string('1.5')
        return cls(tuple(mods), version)

    @cached_property
    def active_package_ids(self) -> set[str]:
        return {mod.package_id for mod in self.mods}

    @cached_property
    def active_package_names(self) -> set[str]:
        return {mod.about.name for mod in self.mods if mod.about.name}


def load_mod_infos(paths: Path|Sequence[Path]) -> list[Mod]:
    if isinstance(paths, Path):
        if not paths.is_dir():
            return []
        if is_mod_folder(paths):
            return [Mod.load(paths)]
        return load_mod_infos(list(paths.iterdir()))
    
    result = []
    for p in paths:
        result.extend(load_mod_infos(p))

    return result


def is_mod_folder(path: Path) -> bool:
    p = path.joinpath('About', 'About.xml')
    return p.exists() and p.is_file()


def read_modlist(filepath: Path) -> tuple[list[str], list[str]]:
    """
    Read and parse the modlist XML file.


    Args:
        filepath (Path): The path to the modlist XML file.

    Returns:
        (active mods, known expansions)

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

    return cast(list[str], mods), cast(list[str], known_expansions)

