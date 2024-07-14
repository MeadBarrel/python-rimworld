from functools import cached_property
from pydantic_settings import BaseSettings, SettingsConfigDict, TomlConfigSettingsSource
from pydantic import computed_field
from pathlib import Path



class Settings(BaseSettings):
    rimworld_appdata_folder: Path
    rimworld_folder: Path
    rimworld_workshop_folder: Path
    rimworld_local_mods_folder: Path

    model_config = SettingsConfigDict(toml_file="config.toml", json_file='config.json', cli_parse_args=True)

    @classmethod
    def settings_customise_sources(cls, settings_cls, **_) :
        return (TomlConfigSettingsSource(settings_cls),)    

    @computed_field
    @cached_property
    def rimworld_config_folder(self) -> Path:
        return self.rimworld_appdata_folder.joinpath('Config')

    @computed_field
    @cached_property
    def rimworld_modlist_filename(self) -> Path:
        return self.rimworld_config_folder.joinpath('ModsConfig.xml')

    @computed_field
    @property
    def expansions_folder(self) -> Path:
        return self.rimworld_folder.joinpath('Data')

    @computed_field
    @property
    def mod_folders(self) -> list[Path]:
        return [
                self.expansions_folder, 
                self.rimworld_workshop_folder, 
                self.rimworld_local_mods_folder
                ]

    

def create_settings() -> Settings:
    """ just a helper function to avoid type: ignore everywhere """
    return Settings(_cli_parse_args=[])  # type: ignore
