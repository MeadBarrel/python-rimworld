# RimWorld XML library

This library is designed to assist with writing mods and mod patches for RimWorld. 
It provides functionality to load game data into an xml file and apply patches to it.

## Basic Usage

```python
from rimworld.world import World

World.from_settings()

print(xml.xpath('/Defs/ThingDef[defName="mything"]'))
```



