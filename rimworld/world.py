from dataclasses import dataclass
import logging
from os import walk
from pathlib import Path
from typing import Self, Sequence
from lxml import etree
from rimworld.mod import Mod
from rimworld.patch.patcher import WorldPatcher

from rimworld.patch.proto import PatchContext, Patcher
from rimworld.settings import Settings
from rimworld.xml import find_xmls, load_xml, merge
from .worldsettings import WorldSettings
from typing import cast


@dataclass(frozen=True)
class World:
    settings: WorldSettings
    xml: etree._ElementTree
    patcher: Patcher|None

    @classmethod
    def from_settings(
            cls, 
            settings: Settings|None=None, 
            patcher: Patcher|None=None,
            add_metadata: bool=False,
            ) -> Self:
        world_settings = WorldSettings.from_settings(settings)
        return cls.new(world_settings, patcher, add_metadata)
        

    @classmethod
    def new(cls, settings: WorldSettings, patcher: Patcher|None=None, add_metadata: bool=False) -> Self:
        patcher = patcher or WorldPatcher()
        xml = etree.ElementTree(etree.Element('Defs'))
        context = PatchContext(xml, settings, patcher)
        for mod in settings.mods:
            merge_mod_data(settings, xml, mod, add_metadata=add_metadata)
            apply_mod_patches(context, mod)
        return cls(
                settings,
                xml,
                patcher,
                )



def merge_mod_data(
        settings: WorldSettings, 
        xml: etree._ElementTree, 
        mod: Mod,
        add_metadata: bool=False,
        ):
    logging.getLogger(__name__).info(f'Loading mod data: {mod}')
    for path in mod.get_mod_folders(settings.version, settings.active_package_ids):
        defs_folder = path.joinpath('Defs')
        if not defs_folder.is_dir():
            continue
        for (dir_path, _, filenames) in defs_folder.walk():
            for filename in filenames:
                xml_path = dir_path.joinpath(filename)
                if xml_path.suffix != '.xml':
                    continue
                logging.getLogger(__name__).info(f'Merging file: {str(xml_path)}')
                file_xml = load_xml(xml_path)

                metadata = {'added_by_mod': mod.package_id} if add_metadata else None

                merge(xml, file_xml, metadata=metadata)


def apply_mod_patches(context: PatchContext, mod: Mod):
    logging.getLogger(__name__).info(f'Applying mod patches: {mod}')
    for path in mod.get_mod_folders(context.settings.version, context.settings.active_package_ids):
        patches_folder = path.joinpath('Patches')
        if not patches_folder.is_dir():
            continue
        for (dir_path, _, filenames) in patches_folder.walk():
            for filename in filenames:
                xml_path = dir_path.joinpath(filename)
                if xml_path.suffix != '.xml':
                    continue
                logging.getLogger(__name__).info(f'Applying patches from {str(xml_path)}')
                file_xml = load_xml(xml_path)
                context.patch(file_xml)


