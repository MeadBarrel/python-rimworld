import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Collection, Self, Sequence

from lxml import etree

from rimworld.gameversion import GameVersion
from rimworld.mod import Mod, is_mod_folder
from rimworld.patch import WorldPatcher
from rimworld.patch.proto import PatchContext, Patcher
from rimworld.xml import load_xml, merge

DEFAULT_GAME_VERSION = GameVersion("1.5")


@dataclass(frozen=True)
class World:
    """A convenience class for easy use"""

    mod_paths: Collection[Path]
    active_package_ids: Sequence[str]
    mods_collection: Collection[Mod]
    xml: etree._ElementTree
    patcher: Patcher

    @classmethod
    def create(
        cls,
        mods: Collection[Path | str | Mod],
        active_package_ids: Sequence[str],
        patcher: Patcher | None = None,
        game_version: GameVersion | str = DEFAULT_GAME_VERSION,
    ) -> Self:
        """Create and load a new world from mod paths and active package ids"""
        game_version = GameVersion(game_version)
        patcher = patcher or WorldPatcher()

        mods_collection: list[Mod] = []
        mod_paths = []

        for mod in mods:
            if isinstance(mod, Mod):
                mods_collection.append(mod)
                mod_paths.append(mod.path)
                continue

            if isinstance(mod, str):
                mod = Path(mod)

            mod_paths.append(mod)

            if is_mod_folder(mod):
                mods_collection.append(Mod.load(mod))
            else:
                for folder in mod.iterdir():
                    if is_mod_folder(folder):
                        mods_collection.append(Mod.load(folder))

        xml = etree.ElementTree(etree.Element("Defs"))
        active_package_ids_ = set(active_package_ids)
        active_mods = [
            mod for mod in mods_collection if mod.package_id in active_package_ids
        ]
        patch_context = PatchContext(
            xml,
            active_package_ids_,
            active_package_names={
                mod.about.name for mod in active_mods if mod.about.name is not None
            },
        )

        for mod in mods_collection:
            for mod_folder in mod.mod_folders(game_version, active_package_ids):
                for def_file in mod_folder.def_files():
                    logging.getLogger(__name__).info("Merging def file %s", def_file)
                    def_xml = load_xml(def_file)
                    merge(xml, def_xml, {"added_by_mod": mod.package_id})

                for patch_file in mod_folder.patch_files():
                    logging.getLogger(__name__).info(
                        "Applying patch file %s", patch_file
                    )
                    patch_xml = load_xml(patch_file)
                    patcher.patch(patch_xml, patch_context)

        return cls(
            mod_paths=mod_paths,
            active_package_ids=active_package_ids,
            mods_collection=mods_collection,
            patcher=patcher,
            xml=xml,
        )
