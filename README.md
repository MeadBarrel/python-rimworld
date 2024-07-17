> [!CAUTION]
> This is a heavily WIP project

# RimWorld XML library

This library is designed to assist with writing mods and mod patches for RimWorld. 
It provides functionality to load game data into an xml file and apply patches to it.

## Basic usage

The package provides a convenience function `load_world` for when you just need to
load the rimworld's xml data, apply patches, and then explore the resulting xml as you
like.

```python
from pathlib import Path

from rimworld import load_world

# First let's prepare some paths (i'm using wsl2):
RIMWORLD_CORE_PACKAGES = Path("/mnt/e/steam/steamapps/common/RimWorld/Data")
RIMWORLD_LOCAL_MODS = Path("/mnt/e/steam/steamapps/common/Rimworld/Mods")
RIMWORLD_STEAM_MODS = Path("/mnt/e/steam/steamapps/workshop/content/294100")
RIMWORLD_MODSCONFIG_FOLDER = Path(
    "/mnt/c/Users/lai/AppData/LocalLow/Ludeon Studios/"
    "RimWorld by Ludeon Studios/Config/ModsConfig.xml"
)

world = load_world(
    mod_folders=[RIMWORLD_CORE_PACKAGES, RIMWORLD_LOCAL_MODS, RIMWORLD_STEAM_MODS],
    modsconfig_folder=RIMWORLD_MODSCONFIG_FOLDER,
)

print(world.xpath("/Defs/ThingDef/label/text()"))
```

## Slightly more advanced usage

If you need something more advanced, you can go lower level.

Here is basically what `load_world` from the above example does:

```python
from pathlib import Path

from lxml import etree

from rimworld.mod import ModsConfig, load_mods, select_mods
from rimworld.patch import PatchContext, get_operation
from rimworld.xml import load_xml, merge

# First let's prepare some paths (i'm using wsl2):
RIMWORLD_CORE_PACKAGES = Path("/mnt/e/steam/steamapps/common/RimWorld/Data")
RIMWORLD_LOCAL_MODS = Path("/mnt/e/steam/steamapps/common/Rimworld/Mods")
RIMWORLD_STEAM_MODS = Path("/mnt/e/steam/steamapps/workshop/content/294100")
RIMWORLD_MODSCONFIG_FOLDER = Path(
    "/mnt/c/Users/lai/AppData/LocalLow/Ludeon Studios/"
    "RimWorld by Ludeon Studios/Config/ModsConfig.xml"
)

# We know where our mods are, but we need to load information about them
# This will take a few seconds as the script loads About.xml files
mods_collection = list(
    load_mods(RIMWORLD_CORE_PACKAGES, RIMWORLD_LOCAL_MODS, RIMWORLD_STEAM_MODS)
)

# Now let's load game version, known expansions, and a list of active mods
mods_config = ModsConfig.load(RIMWORLD_MODSCONFIG_FOLDER)

# Select mods from our mods collection which are active
active_mods = list(select_mods(mods_collection, package_id_in=mods_config.active_mods))

# Prepare patching context - this is needed for proper patching
patch_context = PatchContext(
    active_package_ids={m.package_id for m in active_mods},
    active_package_names={m.about.name for m in active_mods if m.about.name},
)

# Create an empty xml tree
tree = etree.ElementTree(etree.Element("Defs"))

# And the final step
for mod in active_mods:
    for def_file in mod.def_files(mods_config):
        merge(tree, load_xml(def_file))
    for patch_file in mod.patch_files(mods_config):
        patch_operation_nodes = load_xml(patch_file).getroot().findall("Operation")
        for patch_operation_node in patch_operation_nodes:
            patch_operation = get_operation(patch_operation_node)
            patch_operation(tree, patch_context)
```
