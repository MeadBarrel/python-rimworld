""" Common serializers used by patch operations """

from copy import deepcopy
from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterator

from lxml import etree

from rimworld.error import MalformedPatchError
from rimworld.xml import ElementXpath, Xpath

__all__ = [
    "SafeElement",
    "Order",
    "ensure_xpath",
    "ensure_xpath_elt",
    "ensure_value",
    "ensure_element",
    "get_order",
]


@dataclass(frozen=True)
class SafeElement:
    """Wrapper around _Element, making sure it cannot be accessed and modified directly"""

    _element: etree._Element

    def copy(self) -> etree._Element:
        """Return a copy of the contained element"""
        return deepcopy(self._element)


class Order(Enum):
    """Tells where to insert or add an element"""

    APPEND = auto()
    PREPEND = auto()


def ensure_xpath(
    xml: etree._Element,
) -> Xpath:
    """Deserialize <xpath> element as Xpath object"""
    elt = xml.find("xpath")
    if elt is None:
        raise MalformedPatchError("Element not found: xpath")
    if not elt.text:
        raise MalformedPatchError("xpath element has no text")
    xpath = "/" + elt.text.lstrip("/")
    return Xpath.choose(xpath)


def ensure_xpath_elt(
    xml: etree._Element,
) -> ElementXpath:
    """Deserialize <xpath> element as ElementXpath object"""
    result = ensure_xpath(xml)
    if not isinstance(result, ElementXpath):
        raise MalformedPatchError("Only ElementXpath is accepted")
    return result


def ensure_value(xml: etree._Element) -> SafeElement:
    """Return <value> node as SafeElement or string"""
    elt = xml.find("value")
    if elt is None:
        raise MalformedPatchError("Value tag is not present")
    if elt.text is not None and len(elt):
        raise MalformedPatchError("Value node cannot have both text and child nodes")
    return SafeElement(elt)


def ensure_element(xml: etree._Element, tag: str) -> etree._Element:
    """Returns an element with a tag `tag` or raises MalformedPatchError"""
    elt = xml.find(tag)
    if elt is None:
        raise MalformedPatchError(f"Element not found: {tag}")
    return elt


def get_order(xml: etree._Element, default=Order.APPEND) -> Order:
    """Returns <order> as Order enum"""

    order_elt = xml.find("order")
    if order_elt is None:
        return default
    match order_elt.text:
        case "Append":
            return Order.APPEND
        case "Prepend":
            return Order.PREPEND
        case _:
            raise MalformedPatchError("order should be either Append or Prepend")
