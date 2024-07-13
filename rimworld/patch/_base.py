from dataclasses import dataclass
from lxml import etree
from copy import deepcopy

from rimworld.xml import Xpath


__all__ = [
        'MalformedPatchError',
        'PatchError',
        'SafeElement',
        'get_xpath',
        'get_value',
        'get_value_elt',
        'get_text',
        'get_element',
        'get_order_append',
        ]


class MalformedPatchError(Exception):
    pass

class PatchError(Exception):
    pass


@dataclass(frozen=True)
class SafeElement:
    element: etree._Element

    def copy(self) -> etree._Element:
        return deepcopy(self.element)


def get_xpath(xml: etree._Element) -> Xpath:
    elt = xml.find('xpath')
    if elt is None:
        raise MalformedPatchError('Element not found: xpath')
    if not elt.text:
        raise MalformedPatchError('xpath element has no text')
    xpath = '/' + elt.text.lstrip('/')
    return Xpath.choose(xpath)

    
def get_value(xml: etree._Element) -> list[SafeElement]|str:
    elt = xml.find('value')
    if elt is None:
        raise PatchError('Element not found: value')
    if not len(elt):
        return elt.text or ''
    return [SafeElement(e) for e in elt]


def get_value_elt(xml: etree._Element) -> list[SafeElement]:
    elt = xml.find('value')
    if elt is None:
        raise PatchError('Element not found: value')
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

def get_order_append(xml: etree._Element, default: bool) -> bool:
    order_elt = xml.find('order')
    if order_elt is not None:
        if not order_elt.text or order_elt.text not in ('Prepend', 'Append'):
            raise MalformedPatchError('order should be either Append or Prepend')
        return order_elt.text == 'Append'
    return default

