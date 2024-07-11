from pathlib import Path
from lxml import etree
from rimworld import find_xmls
import pytest

from rimworld.mod import Mod
from rimworld.patch import BasePatcher
from rimworld.xml import load_xml


def make_parameters():
    result = []

    mods = [Mod.load(p) for p in Path(__file__).parent.joinpath('mods').iterdir() if p.is_dir()]
    data_files = [(p, load_xml(p)) for p in find_xmls(Path(__file__).parent.joinpath('patches'))]

    for filename, data_file in data_files:
        for case in data_file.findall('Case'):
            name_elt = case.find('Name')
            name = name_elt.text if name_elt is not None else None
            defs = case.find('Defs')
            patch = case.find('Patch')
            expected = case.find('Expected')
            assert defs is not None and patch is not None and expected is not None
            mods_used_elt = case.find('Mods')
            if mods_used_elt is not None:
                mods_used_pids = [
                        li.text
                        for li in mods_used_elt
                        if li.text
                        ]
                mods_used = [
                        mod
                        for mod in mods
                        if mod.package_id in mods_used_pids
                        ]
            else:
                mods_used = []
            result.append((
                    str(filename),
                    name,
                    mods_used,
                    defs,
                    patch,
                    expected,
                    ))
    return result

parameters = make_parameters()


@pytest.mark.parametrize(('file', 'case', 'mods', 'defs', 'patch', 'expected'), parameters)
def test_patches_dd(
        file: str, 
        case: str|None, 
        mods: list[Mod], 
        defs: etree._Element,
        patch: etree._Element,
        expected: etree._Element
        ):
    _unused(file)
    _unused(case)
    patcher = BasePatcher(mods)
    tree = etree.ElementTree(defs)
    patcher.patch(tree, patch)
    
    expected.tag = 'Defs'
    assert_xml_eq(defs, expected)


def _unused(_):
    pass


def assert_xml_eq(e1, e2, path=''):
    if not isinstance(e1, etree._Element):
        raise AssertionError(f'e1 ({e1}) is {type(e1)}, not _Element')
    if not isinstance(e2, etree._Element):
        raise AssertionError(f'e2 ({e2}) is {type(e2)}, not _Element')

    # Compare tags

    if e1.tag != e2.tag:
        raise AssertionError(f"Tags do not match at {path}: {e1.tag} != {e2.tag}")
    
    # Compare text
    if (e1.text or '').strip() != (e2.text or '').strip():
        raise AssertionError(f"Text does not match at {path}: '{e1.text}' != '{e2.text}'")
    
    # Compare tails
    if (e1.tail or '').strip() != (e2.tail or '').strip():

        raise AssertionError(f"Tails do not match at {path}: '{e1.tail}' != '{e2.tail}'")
    
    # Compare attributes
    if e1.attrib != e2.attrib:
        raise AssertionError(f"Attributes do not match at {path}: {e1.attrib} != {e2.attrib}")
    
    # Compare children
    if len(e1) != len(e2):
        print('NOMATCH')
        print(str(etree.tostring(e1, pretty_print=True)))
        print(str(etree.tostring(e2, pretty_print=True)))
        raise AssertionError(f"Number of children do not match at {path}: {len(e1)} != {len(e2)}")
    
    # Recursively compare children
    for i, (c1, c2) in enumerate(zip(e1, e2)):
        assert_xml_eq(c1, c2, path=f"{path}/{e1.tag}[{i}]")

