from dataclasses import dataclass
from typing import Generic, Protocol, cast
from lxml import etree
from pathlib import Path


FALLBACK_ENCODINGS = ['utf-16', 'latin-1', 'cp1252', 'utf32', 'ascii']


class DifferentRootsError(Exception):
    """
    Exception raised when attempting to merge XML trees with different root elements.
    """
    pass


@dataclass(frozen=True)
class TextParent:
    node: etree._Element

    @property
    def text(self) -> str:
        assert self.node.text is not None
        return self.node.text

    @text.setter
    def text(self, value):
        self.node.text = value

    def __str__(self) -> str:
        return self.text


@dataclass(frozen=True)
class AttributeParent:
    node: etree._Element
    attribute: str

    @property
    def value(self):
        assert self.node.get(self.attribute) is not None
        return self.node.get(self.attribute)

    @value.setter
    def value(self, value):
        self.node.set(self.attribute, value)



class Xpath[T]:
    @staticmethod
    def choose(xpath: str) -> 'Xpath':
        if xpath.endswith('text()'):
            return TextXpath(f'{xpath}/..')
        if xpath.rsplit('/', 1)[-1].startswith('@'):
            return AttributeXpath(f'{xpath}/..', xpath.rsplit('/', 1)[-1][1:])
        return ElementXpath(xpath)

    def search(self, xml: etree._ElementTree|etree._Element) -> list[T]:
        ...


@dataclass(frozen=True)
class ElementXpath(Xpath[etree._Element]):
    xpath: str

    def search(self, xml: etree._ElementTree|etree._Element) -> list[etree._Element]:
        result = xml.xpath(self.xpath)
        assert isinstance(result, list)
        assert all(isinstance(item, etree._Element) for item in result)
        return cast(list[etree._Element], result)


@dataclass(frozen=True)
class AttributeXpath(Xpath[AttributeParent]):
    xpath: str
    attribute: str

    def search(self, xml: etree._ElementTree | etree._Element) -> list[AttributeParent]:
        result = xml.xpath(self.xpath)
        assert isinstance(result, list)
        assert all(isinstance(item, etree._Element) and item.get(self.attribute) is not None for item in result)
        return [AttributeParent(cast(etree._Element, item), self.attribute) for item in result]


@dataclass(frozen=True)
class TextXpath(Xpath[TextParent]):
    xpath: str

    def search(self, xml: etree._ElementTree | etree._Element) -> list[TextParent]:
        result = xml.xpath(self.xpath)
        assert isinstance(result, list)
        assert all(isinstance(item, etree._Element) and item.text is not None for item in result)
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
    with filepath.open('rb') as f:
        content = f.read()
        return etree.ElementTree(etree.fromstring(content, parser=parser))


def merge(merge_to: etree._ElementTree, merge_with: etree._ElementTree) -> int:
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
        raise DifferentRootsError(f'{merge_to_root.tag} != {merge_with_root.tag}')

    added = 0

    for node in merge_with_root.iterchildren():
        merge_to_root.append(node)
        added += 1

    return added


def empty_defs() -> etree._ElementTree:
    """
    Creates an empty XML tree with the root tag 'Defs'.


    Returns:
        etree._Element: Root element of the created XML tree with tag 'Defs'.
    """
    return etree.ElementTree(etree.Element('Defs'))


def find_xmls(path: Path) -> list[Path]:
    """
    Helper function to find XML files in the given path.


    Args:
        path (Path): Filesystem path to search for XML files.

    Returns:
        list[Path]: List of paths to XML files.
    """
    result = []
    for p in path.iterdir():
        if p.is_dir():
            result.extend(find_xmls(p))
        if p.suffix == '.xml':
            result.append(p)
    return result

