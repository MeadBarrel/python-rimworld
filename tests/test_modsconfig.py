""" Tests for rimworld.mod.ModsConfig """

from pathlib import Path

from rimworld.gameversion import GameVersion
from rimworld.mod import ModsConfig
from rimworld.xml import assert_xml_eq, load_xml


def test_deserialization():
    """Test deserialization"""
    file_path = Path("./testdata/config/expansions_only/Config/ModsConfig.xml")
    config = ModsConfig.load(file_path)

    assert config == ModsConfig(
        version=GameVersion.new("1.5.4104 rev435"),
        active_mods=[
            "ludeon.rimworld",
            "ludeon.rimworld.royalty",
            "ludeon.rimworld.ideology",
            "ludeon.rimworld.biotech",
            "ludeon.rimworld.anomaly",
        ],
        known_expansions=[
            "ludeon.rimworld.royalty",
            "ludeon.rimworld.ideology",
            "ludeon.rimworld.biotech",
            "ludeon.rimworld.anomaly",
        ],
    )


def test_serialization():
    """Test deserialization"""
    file_path = Path("./testdata/config/expansions_only/Config/ModsConfig.xml")
    xml = load_xml(file_path)

    config = ModsConfig(
        version=GameVersion.new("1.5.4104 rev435"),
        active_mods=[
            "ludeon.rimworld",
            "ludeon.rimworld.royalty",
            "ludeon.rimworld.ideology",
            "ludeon.rimworld.biotech",
            "ludeon.rimworld.anomaly",
        ],
        known_expansions=[
            "ludeon.rimworld.royalty",
            "ludeon.rimworld.ideology",
            "ludeon.rimworld.biotech",
            "ludeon.rimworld.anomaly",
        ],
    )

    serialized = config.to_xml()

    assert_xml_eq(serialized.getroot(), xml.getroot())
