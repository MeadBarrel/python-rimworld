""" rimwold.xml """

from lxml import etree

from rimworld.xml import make_element


def test_make_element_with_parent():
    """Test if make_element attaches the node to the parent"""
    parent = etree.Element("parent")
    child = make_element("child", parent=parent)
    assert parent.find("child") is child
