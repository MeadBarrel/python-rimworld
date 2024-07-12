from dataclasses import dataclass
from enum import Enum, auto
from lxml import etree
from copy import deepcopy
from typing import Self, cast
from rimworld.base import MalformedPatchError


__all__ = [
        'SafeElement',
        'get_xpath',
        'get_value',
        'get_text',
        'get_element',
        'xpath_elements',
        'get_order_append',
        ]


@dataclass(frozen=True)
class SafeElement:
    element: etree._Element

    def copy(self) -> etree._Element:
        return deepcopy(self.element)




def get_xpath(xml: etree._Element) -> str:
    elt = xml.find('xpath')
    if elt is None:
        raise MalformedPatchError('Element not found: xpath')
    if not elt.text:
        raise MalformedPatchError('xpath element has no text')
    xpath = elt.text
    if not xpath.startswith('/'):
        xpath = '/' + xpath
    return xpath
    
    
def get_value(xml: etree._Element) -> list[SafeElement]:
    elt = xml.find('value')
    if elt is None:
        raise MalformedPatchError('Element not found: value')
    return [SafeElement(e) for e in elt]


def get_text(xml: etree._Element, tag: str) -> str:
    elt = xml.find(tag)
    if elt is None:
        raise MalformedPatchError(f'Element not found: {tag}')
    return elt.text or ''

def get_element(xml: etree._Element, tag: str) -> etree._Element:
    elt = xml.find(tag)
    if elt is None:
        raise MalformedPatchError(f'Element not found: {tag}')
    return elt


def xpath_elements(xml: etree._ElementTree, xpath: str) -> list[etree._Element]:
    found = xml.xpath(xpath)

    if isinstance(found , etree._Element):
        found = [found]
    if not (isinstance(found, list) and all(isinstance(x, etree._Element) for x in found)):
        raise MalformedPatchError('xpath returned unexpected results')
    return cast(list[etree._Element], found)


def get_order_append(xml: etree._Element, default: bool) -> bool:
    order_elt = xml.find('order')
    if order_elt is not None:
        if not order_elt.text or order_elt.text not in ('Prepend', 'Append'):
            raise MalformedPatchError('order should be either Append or Prepend')
        return order_elt.text == 'Append'
    return default

