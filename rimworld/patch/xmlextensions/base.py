""" Common serializers used in XmlExtensions """

from enum import Enum, auto

from lxml import etree

from rimworld.error import MalformedPatchError


class Compare(Enum):
    """Compare value of the <compare> node"""

    NAME = auto()
    INNER_TEXT = auto()
    BOTH = auto()


def get_safety_depth(node: etree._Element) -> int:
    """Get safetyDepth value"""
    safety_depth = -1
    if (n := node.find("safetyDepth")) is not None:
        if not n.text:
            raise MalformedPatchError("incorrect safetyDepth")
        try:
            safety_depth = int(n.text)
        except ValueError as e:
            raise MalformedPatchError("incorrect safetyDepth") from e
    return safety_depth


def set_safety_depth(node: etree._Element, safety_depth: int):
    """Serialize safety depth into the node"""
    if safety_depth == -1:
        return
    n = etree.Element("safetyDepth")
    n.text = str(safety_depth)
    node.append(n)


def get_compare(node: etree._Element) -> Compare:
    """Get <compare> node value"""
    match node.find("compare"):
        case None:
            return Compare.NAME
        case etree._Element(text="Name"):
            return Compare.NAME
        case etree._Element(text="InnerText"):
            return Compare.INNER_TEXT
        case etree._Element(text="Both"):
            return Compare.BOTH
        case _:
            raise MalformedPatchError("Incorrect compare value")


def set_compare(node: etree._Element, compare: Compare):
    """Serialize Compare into node"""
    match compare:
        case Compare.NAME:
            return
        case Compare.INNER_TEXT:
            n = etree.Element("compare")
            n.text = "InnerText"
            node.append(n)
        case Compare.BOTH:
            n = etree.Element("compare")
            n.text = "Both"
            node.append(n)


def get_check_attributes(node: etree._Element) -> bool:
    """read <checkAttributes> node as bool"""
    match node.find("checkAttributes"):
        case None:
            return False
        case etree._Element(text="false"):
            return False
        case etree._Element(text="true"):
            return True
        case _:
            raise MalformedPatchError("Incorrect checkAttributes value")


def set_check_attributes(node: etree._Element, check_attributes: bool):
    """Serialize check_attributes into <checkAttributes> node"""
    if not check_attributes:
        return
    n = etree.Element("checkAttributes")
    n.text = "true"
    node.append(n)


def get_existing_node(
    compare: Compare, node: etree._Element, value: etree._Element
) -> etree._Element | None:
    """Check if a node exists"""
    match compare:
        case Compare.NAME:
            if (n := node.find(value.tag)) is not None:
                return n
        case Compare.INNER_TEXT:
            for n in node:
                if n.text == value.text:
                    return n
        case Compare.BOTH:
            if (n := node.find(value.tag)) is not None and n.text == value.text:
                return n
    return None
