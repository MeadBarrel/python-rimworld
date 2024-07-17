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
    "xml_to_string",
    "assert_xml_eq",
    "assert_xml_eq_ignore_order",
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
    if parent is not None:
        parent.append(result)
    return result


def element_text_or_none(element: etree._Element | None, strip=True) -> str | None:
    """Convenience function to return element's text"""
    if element is None:
        return None
    text = element.text
    if text is None:
        return None
    if strip:
        text = text.strip()
    return text


def ensure_element_text(element: etree._Element | None, strip=True) -> str:
    """Convenience function to return element's text

    raises an exception if either element is None or has no text
    """
    if element is None:
        raise RuntimeError("element must be present")
    if element.text is None:
        raise RuntimeError("element must have text")
    if strip:
        return element.text.strip()
    return element.text


def serialize_as_list(parent: etree._Element, values: Sequence[XMLSerializable]):
    """Serialize values into a list

    Example:
        >>> @dataclass
        ... class Dummy:
        ...     text: str
        ...
        ...     def to_xml(self, parent):
        ...         make_element('dummy', self.text, parent=parent)
        ...
        >>> dummies = [Dummy('i am a dummy'), Dummy('he is a dummy')]
        >>> node = make_element('list_of_dummies')
        >>> serialize_as_list(node, dummies)
        >>> print(xml_to_string(node))
        <list_of_dummies>
          <li>
            <dummy>i am a dummy</dummy>
          </li>
          <li>
            <dummy>he is a dummy</dummy>
          </li>
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
        ... class Dummy:
        ...     text: str
        ...
        ...     @classmethod
        ...     def from_xml(cls, node):
        ...         return cls(node.text)
        ...
        >>> raw = '<node><li>i am a dummy</li><li>he is a dummy</li></node>'
        >>> node = etree.fromstring(raw)
        >>> deserialize_from_list(node, Dummy)
        [Dummy(text='i am a dummy'), Dummy(text='he is a dummy')]
    """

    return [cls_.from_xml(li) for li in parent.findall("li")]


def deserialize_strings_from_list(parent: etree._Element, strip=True) -> list[str]:
    """Deserialize strings from a list"""
    result = []
    for li in parent.findall("li"):
        text = element_text_or_none(li)
        if text:
            if strip:
                text = text.strip()
            result.append(text)
    return result


def xml_to_string(node: etree._ElementTree | etree._Element):
    """Convert xml to pretty-printed utf string"""
    return etree.tostring(node, pretty_print=True, encoding="utf-8").decode("utf-8")


def assert_xml_eq(e1: etree._Element, e2: etree._Element, path=""):
    """test two elements for equality"""
    if not isinstance(e1, etree._Element):
        raise AssertionError(f"e1 ({e1}) is {type(e1)}, not _Element")
    if not isinstance(e2, etree._Element):
        raise AssertionError(f"e2 ({e2}) is {type(e2)}, not _Element")

    # Compare tags

    if e1.tag != e2.tag:
        raise AssertionError(f"Tags do not match at {path}: {e1.tag} != {e2.tag}")

    # Compare text
    if (e1.text or "").strip() != (e2.text or "").strip():
        raise AssertionError(
            f"Text does not match at {path}: '{e1.text}' != '{e2.text}'"
        )

    # Compare tails
    if (e1.tail or "").strip() != (e2.tail or "").strip():

        raise AssertionError(
            f"Tails do not match at {path}: '{e1.tail}' != '{e2.tail}'"
        )

    # Compare attributes
    if e1.attrib != e2.attrib:
        raise AssertionError(
            f"Attributes do not match at {path}: {e1.attrib} != {e2.attrib}"
        )

    # Compare children
    if len(e1) != len(e2):
        print("NOMATCH")
        print(str(etree.tostring(e1, pretty_print=True)))
        print(str(etree.tostring(e2, pretty_print=True)))
        raise AssertionError(
            f"Number of children do not match at {path}: {len(e1)} != {len(e2)}"
        )

    # Recursively compare children
    for i, (c1, c2) in enumerate(zip(e1, e2)):
        assert_xml_eq(c1, c2, path=f"{path}/{e1.tag}[{i}]")


from lxml import etree


def assert_xml_eq_ignore_order(e1: etree._Element, e2: etree._Element, path=""):
    """Test two elements for equality, ignoring the order of elements."""
    if not isinstance(e1, etree._Element):
        raise AssertionError(f"e1 ({e1}) is {type(e1)}, not _Element")
    if not isinstance(e2, etree._Element):
        raise AssertionError(f"e2 ({e2}) is {type(e2)}, not _Element")

    # Compare tags
    if e1.tag != e2.tag:
        raise AssertionError(f"Tags do not match at {path}: {e1.tag} != {e2.tag}")

    # Compare text
    if (e1.text or "").strip() != (e2.text or "").strip():
        raise AssertionError(
            f"Text does not match at {path}: '{e1.text}' != '{e2.text}'"
        )

    # Compare tails
    if (e1.tail or "").strip() != (e2.tail or "").strip():
        raise AssertionError(
            f"Tails do not match at {path}: '{e1.tail}' != '{e2.tail}'"
        )

    # Compare attributes
    if e1.attrib != e2.attrib:
        raise AssertionError(
            f"Attributes do not match at {path}: {e1.attrib} != {e2.attrib}"
        )

    # Compare children
    if len(e1) != len(e2):
        raise AssertionError(
            f"Number of children do not match at {path}: {len(e1)} != {len(e2)}"
        )

    # Sort children by tag and text for comparison
    def sort_key(elem):
        return (elem.tag, (elem.text or "").strip())

    sorted_e1_children = sorted(e1, key=sort_key)
    sorted_e2_children = sorted(e2, key=sort_key)

    # Recursively compare children
    for i, (c1, c2) in enumerate(zip(sorted_e1_children, sorted_e2_children)):
        assert_xml_eq(c1, c2, path=f"{path}/{e1.tag}[{i}]")
