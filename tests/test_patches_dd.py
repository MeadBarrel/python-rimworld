from pathlib import Path

import pytest
from lxml import etree

from rimworld.mod import Mod
from rimworld.patch import PatchContext, get_operation
from rimworld.util import unused
from rimworld.xml import assert_xml_eq, find_xmls, load_xml


def make_parameters():  # pylint: disable=too-many-locals
    """prepare parameters for the test"""
    result = []

    mods = [
        Mod.load(p)
        for p in Path(__file__).parent.joinpath("mods").iterdir()
        if p.is_dir()
    ]
    data_files = [
        (p, load_xml(p)) for p in find_xmls(Path(__file__).parent.joinpath("patches"))
    ]

    for filename, data_file in data_files:
        for case in data_file.findall("Case"):
            name_elt = case.find("Name")
            name = name_elt.text if name_elt is not None else None
            defs = case.find("Defs")
            patch = case.find("Patch")
            expected = case.find("Expected")
            assert defs is not None and patch is not None and expected is not None
            mods_used_elt = case.find("Mods")
            if mods_used_elt is not None:
                mods_used_pids = [li.text for li in mods_used_elt if li.text]
                mods_used = [mod for mod in mods if mod.package_id in mods_used_pids]
            else:
                mods_used = []
            xml = etree.ElementTree(defs)

            context = PatchContext(
                active_package_ids=set(mod.package_id for mod in mods_used),
                active_package_names=set(
                    mod.about.name for mod in mods_used if mod.about.name
                ),
            )
            result.append(
                (
                    str(filename),
                    name,
                    xml,
                    context,
                    patch,
                    expected,
                )
            )
    return result


parameters = make_parameters()


@pytest.mark.parametrize(
    ("file", "case", "xml", "context", "patch", "expected"), parameters
)
def test_patches_dd(
    file: str,
    case: str | None,
    xml: etree._ElementTree,
    context: PatchContext,
    patch: etree._Element,
    expected: etree._Element,
):
    """Test patch operations"""
    unused(file)
    unused(case)
    for node in patch.findall("Operation"):
        get_operation(node)(xml, context)

    expected.tag = "Defs"
    assert_xml_eq(xml.getroot(), expected)
