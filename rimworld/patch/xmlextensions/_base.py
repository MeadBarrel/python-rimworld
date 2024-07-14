from lxml import etree
from .._base import *
from enum import Enum, auto


class Compare(Enum):
    Name = auto()
    InnerText = auto()
    Both = auto()


def get_safety_depth(node: etree._Element) -> int:
    safety_depth = -1
    if (n := node.find('safetyDepth')) is not None:
        if not n.text:
            raise MalformedPatchError('incorrect safetyDepth')
        try:
            safety_depth = int(n.text)
        except ValueError:
            raise MalformedPatchError('incorrect safetyDepth')
    return safety_depth

def set_safety_depth(node: etree._Element, safety_depth: int):
    if safety_depth == -1:
        return
    n = etree.Element('safetyDepth')
    n.text = str(safety_depth)
    node.append(n)


def get_compare(node: etree._Element) -> Compare:
    match node.find('compare'):
        case None:
            return Compare.Name
        case etree._Element(text="Name"):
            return Compare.Name
        case etree._Element(text="InnerText"):
            return Compare.InnerText
        case etree._Element(text="Both"):
            return Compare.Both
        case _:
            raise MalformedPatchError(f'Incorrect compare value')

def set_compare(node: etree._Element, compare: Compare):
    match compare:
        case Compare.Name:
            return
        case Compare.InnerText:
            n = etree.Element('compare')
            n.text = 'InnerText'
            node.append(n)
        case Compare.Both:
            n = etree.Element('compare')
            n.text = 'Both'
            node.append(n)


def get_check_attributes(node: etree._Element) -> bool:
    match node.find('checkAttributes'):
        case None:
            return False
        case etree._Element(text='false'):
            return False
        case etree._Element(text='true'):
            return True
        case _:
            raise MalformedPatchError(f'Incorrect checkAttributes value')

def set_check_attributes(node: etree._Element, check_attributes: bool):
    if not check_attributes:
        return
    n = etree.Element('checkAttributes')
    n.text = 'true'
    node.append(n)

    

def get_existing_node(compare: Compare, node: etree._Element, value: etree._Element) -> etree._Element|None:
    match compare:
        case Compare.Name:
            if (n := node.find(value.tag)) is not None:
                return n
        case Compare.InnerText:
            for n in node:
                if n.text == value.text:
                    return n
        case Compare.Both:
            if (n:=node.find(value.tag)) is not None and n.text == value.text:
                return n
