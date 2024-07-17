"""Provides PatchOperationSafeAdd"""

from dataclasses import dataclass
from typing import Self

from lxml import etree

from rimworld.error import MalformedPatchError, NoNodesFound
from rimworld.patch.proto import PatchOperation, PatchOperationResult
from rimworld.patch.result import (PatchOperationBasicCounterResult,
                                   PatchOperationFailedResult)
from rimworld.patch.serializers import SafeElement, ensure_value, ensure_xpath
from rimworld.patch.xmlextensions.base import (Compare, get_check_attributes,
                                               get_compare, get_existing_node,
                                               get_safety_depth,
                                               set_check_attributes,
                                               set_compare, set_safety_depth)
from rimworld.xml import ElementXpath


@dataclass(frozen=True)
class PatchOperationSafeAdd(PatchOperation):
    """PatchOperationSafeAdd

    https://github.com/15adhami/XmlExtensions/wiki/XmlExtensions.PatchOperationSafeAdd
    """

    xpath: ElementXpath
    value: SafeElement
    safety_depth: int = -1
    compare: Compare = Compare.NAME
    check_attributes: bool = False

    def __call__(self, xml: etree._ElementTree, *_) -> PatchOperationResult:
        found = self.xpath.search(xml)

        if not found:
            return PatchOperationFailedResult(self, NoNodesFound(str(self.xpath)))

        for node in found:
            for value in self.value.copy():
                self._apply_recursive(node, value, self.safety_depth)

        return PatchOperationBasicCounterResult(self, len(found))

    def _apply_recursive(self, node: etree._Element, value: etree._Element, depth: int):
        existing = get_existing_node(self.compare, node, value)

        if self.check_attributes:
            if set(node.attrib.items()) != set(value.attrib.items()):
                existing = None

        if existing is None:
            node.append(value)
            return

        if depth == 1:
            return

        for sub_value in value:
            self._apply_recursive(existing, sub_value, depth - 1)

    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        """Deserialize from an xml node"""
        xpath = ensure_xpath(node)
        if not isinstance(xpath, ElementXpath):
            raise MalformedPatchError("SafeAdd only works on elements")

        value = ensure_value(node)

        return cls(
            xpath=xpath,
            value=value,
            safety_depth=get_safety_depth(node),
            compare=get_compare(node),
            check_attributes=get_check_attributes(node),
        )

    def to_xml(self, node: etree._Element):
        node.set("Class", "PatchOperationAdd")

        xpath = etree.Element("xpath")
        xpath.text = self.xpath.xpath
        node.append(xpath)

        set_compare(node, self.compare)
        set_check_attributes(node, self.check_attributes)
        set_safety_depth(node, self.safety_depth)

        node.append(self.value.copy())
