""" Test rimworld.mod.ModAbout """

from collections.abc import Iterator
from pathlib import Path

import pytest
from lxml import etree

from rimworld.gameversion import GameVersion
from rimworld.mod import ModAbout
from rimworld.xml import assert_xml_eq_ignore_order, load_xml


def create_abouts() -> Iterator[tuple[str, etree._ElementTree]]:
    """Load some About.xml"""
    folders = (
        Path("./testdata/rimworld_expansions"),
        Path("./testdata/rimworld_local_mods"),
        Path("./testdata/rimworld_steam_mods"),
    )

    for folder in folders:
        for sub_folder in folder.iterdir():
            about_xml = sub_folder.joinpath("About", "About.xml")
            yield str(about_xml), load_xml(about_xml)


def test_deserialize_anomaly():
    """Test deserialization"""
    xml = load_xml(Path("./testdata/rimworld_expansions/Anomaly/About/About.xml"))
    about = ModAbout.from_xml(xml)
    assert about == ModAbout(
        package_id="Ludeon.RimWorld.Anomaly",
        authors=["Ludeon Studios"],
        supported_versions=(GameVersion.new("1.5"),),
        load_after=["Ludeon.RimWorld"],
        steam_app_id="2380740",
        force_load_after=[
            "Ludeon.RimWorld.Royalty",
            "Ludeon.RimWorld.Ideology",
            "Ludeon.RimWorld.Biotech",
        ],
    )


@pytest.mark.parametrize(("filename", "xml"), list(create_abouts()))
def test_serialize_deserialize_sanity(filename: str, xml: etree._ElementTree):
    """Test serialization/deserialization for sanity"""
    deserialized = ModAbout.from_xml(xml)
    serialized = deserialized.to_xml()
    print(filename, [t.tag for t in serialized.getroot()])
    assert_xml_eq_ignore_order(serialized.getroot(), xml.getroot())
