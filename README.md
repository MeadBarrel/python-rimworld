> [!CAUTION]
> This is a heavily WIP project

# RimWorld XML library

This library is designed to assist with writing mods and mod patches for RimWorld. 
It provides functionality to load game data into an xml file and apply patches to it.

## Basic Usage

```python
from rimworld.world import World

World.from_settings()

print(xml.xpath('/Defs/ThingDef[defName="mything"]'))
```


## Settings

rimworld.settings module provide basic settings needed to load mod data. By default they are
loaded from `config.toml` file in current folder, which has the following format:

```toml
rimworld_appdata_folder="<user folder>/AppData/LocalLow/Ludeon Studios/RimWorld by Ludeon Studios/"
rimworld_folder="<steam folder>/steamapps/common/RimWorld"
rimworld_workshop_folder="<steam folder>/steamapps/workshop/content/294100"
rimworld_local_mods_folder="<steam folder>/steamapps/common/RimWorld/Mods"
```

## Advanced Usage
You can customize your world by specifying different versions, modlists, etc

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from pathlib import Path
from rimworld.settings import create_settings
from rimworld.worldsettings import WorldSettings, load_mod_infos
from rimworld.gameversion import GameVersion
from rimworld.world import World

# load config.toml
settings = create_settings()

# set game version
version = GameVersion.from_string('1.5')

# get Path with rimworld Core module and expansions
core_path = settings.expansions
my_mod_path = Path('C:\\Projects\\MyMod')

# load About.xml information about expansions and the mods
mods = load_mod_infos([core_path, my_mod_path])


# Load world
world_settings = WorldSettings(mods, version)
world = World.new(world_settings)

# now just wait for loading to complete
```
