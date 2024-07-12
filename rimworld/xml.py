from lxml import etree
from pathlib import Path


FALLBACK_ENCODINGS = ['utf-16', 'latin-1', 'cp1252', 'utf32', 'ascii']


class DifferentRootsError(Exception):
    """
    Exception raised when attempting to merge XML trees with different root elements.
    """
    pass


def load_xml(filepath: Path) -> etree._ElementTree:
    """
    Loads an XML file and returns its root element.


    Args:
        filepath (Path): Path to the XML file.

    Returns:
        etree._Element: Root element of the loaded XML file.
    """
    parser = etree.XMLParser(recover=True)
    with filepath.open('rb') as f:
        content = f.read()
        etree.ElementTree
        return etree.XML(content, parser=parser)


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


def empty_tree(root_node_tag: str) -> etree._Element:
    """
    Creates an empty XML tree with a specified root tag.


    Args:
        root_node_tag (str): The tag name for the root element.

    Returns:
        etree._Element: Root element of the created XML tree with the specified tag.

    """
    return etree.fromstring(f'<{root_node_tag}></{root_node_tag}>')



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

