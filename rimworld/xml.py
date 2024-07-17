""" Convenience functions for working with XML """

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import (Iterator, Protocol, Self, Sequence, Type, cast,
                    runtime_checkable)

from lxml import etree

from .error import DifferentRootsError

__all__ = [
    "XMLSerializable",
    "TextParent",
    "AttributeParent",
    "Xpath",
    "ElementXpath",
    "AttributeXpath",
    "TextXpath",
    "load_xml",
    "find_xmls",
    "merge",
    "make_element",
    "element_text_or_none",
    "ensure_element_text",
    "serialize_as_list",
    "serialize_strings_as_list",
    "deserialize_from_list",
    "deserialize_strings_from_list",
]


@runtime_checkable
class XMLSerializable(Protocol):
    """Object that can serialize / deserialize to / from xml"""

    def to_xml(self, parent: etree._Element):
        """Serialize into parent"""

    @classmethod
    def from_xml(cls: Type[Self], node: etree._Element) -> Self:
        """Deserialize from node"""
        ...


@dataclass(frozen=True)
class TextParent:
    """Represents an element with text guaranteed to exist"""

    node: etree._Element

    @property
    def text(self) -> str:
        """Text of the element"""
        assert self.node.text is not None
        return str(self.node.text)

    @text.setter
    def text(self, value):
        self.node.text = value

    def __str__(self) -> str:
        return self.text


@dataclass(frozen=True)
class AttributeParent:
    """Represents a node with a specified attribute guaranteed to exist"""

    node: etree._Element
    attribute: str

    @property
    def value(self):
        """Return value of the attribute"""
        assert self.node.get(self.attribute) is not None
        return self.node.get(self.attribute)

    @value.setter
    def value(self, value):
        self.node.set(self.attribute, value)


# T = TypeVar("T")


class Xpath[T](ABC):
    """Represents an XPath expression"""

    xpath: str

    @staticmethod
    def choose(xpath: str) -> "Xpath":
        """Choose an xpath expression instance based on xpath

        anything ending with `text()` will result in TextXpath
        anything ending with @<attribute> will result in AttributeXpath
        the rest will result in ElementXpath

        """
        if xpath.endswith("text()"):
            return TextXpath(f"{xpath}/..")
        if xpath.rsplit("/", 1)[-1].startswith("@"):
            return AttributeXpath(f"{xpath}/..", xpath.rsplit("/", 1)[-1][1:])
        return ElementXpath(xpath)

    @abstractmethod
    def search(self, xml: etree._ElementTree | etree._Element) -> list[T]:
        """Search the xml"""

    def __str__(self) -> str:
        return self.xpath


@dataclass(frozen=True)
class ElementXpath(Xpath[etree._Element]):
    """An xpath that returns an element"""

    xpath: str

    def search(self, xml: etree._ElementTree | etree._Element) -> list[etree._Element]:
        result = xml.xpath(self.xpath)
        assert isinstance(result, list)
        assert all(isinstance(item, etree._Element) for item in result)
        return cast(list[etree._Element], result)


@dataclass(frozen=True)
class AttributeXpath(Xpath[AttributeParent]):
    """An xpath that returns an attribute"""

    xpath: str
    attribute: str

    def search(self, xml: etree._ElementTree | etree._Element) -> list[AttributeParent]:
        result = xml.xpath(self.xpath)
        assert isinstance(result, list)
        assert all(
            isinstance(item, etree._Element) and item.get(self.attribute) is not None
            for item in result
        )
        return [
            AttributeParent(cast(etree._Element, item), self.attribute)
            for item in result
        ]


@dataclass(frozen=True)
class TextXpath(Xpath[TextParent]):
    """An xpath that returns an element's text value"""

    xpath: str

    def search(self, xml: etree._ElementTree | etree._Element) -> list[TextParent]:
        result = xml.xpath(self.xpath)
        assert isinstance(result, list)
        assert all(
            isinstance(item, etree._Element) and item.text is not None
            for item in result
        )
        return [TextParent(cast(etree._Element, item)) for item in result]


def load_xml(filepath: Path) -> etree._ElementTree:
    """
    Loads an XML file and returns its root element.


    Args:
        filepath (Path): Path to the XML file.

    Returns:
        etree._Element: Root element of the loaded XML file.
    """
    parser = etree.XMLParser(recover=True, remove_blank_text=True)
    with filepath.open("rb") as f:
        content = f.read()
        return etree.ElementTree(etree.fromstring(content, parser=parser))


def merge(
    merge_to: etree._ElementTree,
    merge_with: etree._ElementTree,
    metadata: dict[str, str] | None = None,
) -> int:
    """
    Merges two XML elements by appending children from one element to the other.


    Args:
        merge_to (etree._Element): The target element to merge into.
        merge_with (etree._Element): The source element to merge from.

    Raises:
        DifferentRootsError: If the root elements of the two XML trees are different.

    Returns:
        int: The number of children added to the target element.

    """
    merge_to_root = merge_to.getroot()
    merge_with_root = merge_with.getroot()
    if merge_to_root.tag != merge_with_root.tag:
        raise DifferentRootsError(f"{merge_to_root.tag} != {merge_with_root.tag}")

    added = 0

    for node in merge_with_root.iterchildren():
        try:
            for k, v in (metadata or {}).items():
                node.set(k, v)
        except TypeError:
            pass
        merge_to_root.append(node)
        added += 1

    return added


def find_xmls(path: Path) -> Iterator[Path]:
    """Find all .xml files in the given path"""
    for dir_, _, filenames in path.walk():
        for filename in filenames:
            filepath = dir_.joinpath(filename)
            if filepath.suffix == ".xml":
                yield filepath


def make_element(
    tag: str,
    text: str | None = None,
    attributes: dict[str, str] | None = None,
    children: Sequence[etree._Element] | None = None,
    parent: etree._Element | None = None,
):
    """A convenience function to create an xpath element"""
    attributes = attributes or {}
    children = children or []
    result = etree.Element(tag)
    result.text = text
    for k, v in attributes.items():
        result.set(k, v)
    for child in children:
        result.append(child)
    if parent:
        parent.append(result)
    return result


def element_text_or_none(element: etree._Element | None) -> str | None:
    """Convenience function to return element's text"""
    if element is None:
        return None
    return element.text


def ensure_element_text(element: etree._Element | None) -> str:
    """Convenience function to return element's text

    raises an exception if either element is None or has no text
    """
    if element is None:
        raise RuntimeError("element must be present")
    if element.text is None:
        raise RuntimeError("element must have text")
    return element.text


def serialize_as_list(parent: etree._Element, values: Sequence[XMLSerializable]):
    """Serialize values into a list

    Example:

        >>> @dataclass
        >>> class Dummy(XMLSerializable):

        >>>    def to_xml(self, parent: etree._Element):
        >>>         make_element('dummy', self.text, parent=parent)

        >>>     @classmethod
        >>>     def from_xml(cls: Type[Self], node: etree._Element) -> Self:
        >>>         return ensure_element_text(node.find('dummy'))

        >>> dummies = [Dummy('i am a dummy'), Dummy('he is a dummy')]
        >>> node = make_element('list_of_dummies')
        >>> serialize_as_list(node, dummies)
        >>> etree.tostring(node, pretty_print=True).decode('utf-8')
        <list_of_dummies>
            <li>i am a dummy</li>
            <li>he is a dummy</li>
        </list_of_dummies>

    """
    for value in values:
        li = make_element("li", parent=parent)
        value.to_xml(li)


def serialize_strings_as_list(parent: etree._Element, values: Sequence[str]):
    """Serialize strings into a list"""
    for value in values:
        make_element("li", value, parent=parent)


def deserialize_from_list[
    T: XMLSerializable
](parent: etree._Element, cls_: Type[T]) -> list[T]:
    """Deserialize values from a list


    Example:

        >>> @dataclass
        >>> class Dummy(XMLSerializable):
        >>>    text: str

        >>>    def to_xml(self, parent: etree._Element):
        >>>         make_element('dummy', self.text, parent=parent)

        >>>     @classmethod
        >>>     def from_xml(cls: Type[Self], node: etree._Element) -> Self:
        >>>         return ensure_element_text(node.find('dummy'))

        >>> dummies = [Dummy('i am a dummy'), Dummy('he is a dummy')]
        >>> node = make_element('list_of_dummies')
        >>> serialize_as_list(node, dummies)
        >>> print(etree.tostring(node, pretty_print=True).decode('utf-8'))
        >>> xml = "<list_of_dummies><li>i am a dummy</li><li>he is a dummy</li></list_of_dummies>"
        >>> node = etree.fromstring(xml)
        >>> deserialize_fom_list(node, Dummy)
        [Dummy(text='i am a dummy'), Dummy(text='he is a dummy')]

    """

    return [cls_.from_xml(li) for li in parent.findall("li")]


def deserialize_strings_from_list(parent: etree._Element) -> list[str]:
    """Deserialize strings from a list"""
    result = []
    for li in parent.findall("li"):
        text = element_text_or_none(li)
        if text:
            result.append(text)
    return result
