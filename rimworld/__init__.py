from pathlib import Path
from typing import Collection

from lxml import etree

from rimworld.mod import ModsConfig, load_mods, select_mods
from rimworld.patch import PatchContext, get_operation
from rimworld.xml import load_xml, merge

__all__ = ["load_world"]


def load_world(
    mod_folders: Collection[Path], modsconfig_folder: Path
) -> etree._ElementTree:
    """Convenience function to just load the world as Rimworld would do

    Note:
        hopefully
    """

    mods_collection = list(load_mods(*mod_folders))
    mods_config = ModsConfig.load(modsconfig_folder)
    active_mods = list(
        select_mods(mods_collection, package_id_in=mods_config.active_mods)
    )
    patch_context = PatchContext(
        active_package_ids={m.package_id for m in active_mods},
        active_package_names={m.about.name for m in active_mods if m.about.name},
    )

    tree = etree.ElementTree(etree.Element("Defs"))

    for mod in active_mods:
        for def_file in mod.def_files(mods_config):
            merge(tree, load_xml(def_file))
        for patch_file in mod.patch_files(mods_config):
            patch_operation_nodes = load_xml(patch_file).getroot().findall("Operation")
            for patch_operation_node in patch_operation_nodes:
                patch_operation = get_operation(patch_operation_node)
                patch_operation(tree, patch_context)
    return tree
