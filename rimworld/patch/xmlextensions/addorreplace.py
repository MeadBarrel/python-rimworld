""" Provides PatchOperationAddOrReplace """

from dataclasses import dataclass
from typing import Self

from lxml import etree

from rimworld.error import MalformedPatchError, NoNodesFound
from rimworld.patch.proto import PatchOperation, PatchOperationResult
from rimworld.patch.result import (PatchOperationBasicCounterResult,
                                   PatchOperationFailedResult)
from rimworld.patch.serializers import SafeElement, ensure_value, ensure_xpath
from rimworld.xml import ElementXpath

from .base import (Compare, get_check_attributes, get_compare,
                   get_existing_node, set_check_attributes, set_compare)


@dataclass(frozen=True)
class PatchOperationAddOrReplace(PatchOperation):
    """PatchOperationAddOrReplace

    https://github.com/15adhami/XmlExtensions/wiki/XmlExtensions.PatchOperationAddOrReplace
    """

    xpath: ElementXpath
    compare: Compare
    check_attributes: bool
    value: SafeElement

    def __call__(self, xml: etree._ElementTree, *_) -> PatchOperationResult:
        found = self.xpath.search(xml)

        if not found:
            return PatchOperationFailedResult(self, NoNodesFound(str(self.xpath)))

        for node in found:
            for v in self.value.copy():
                existing = get_existing_node(self.compare, node, v)
                if existing is None:
                    node.append(v)
                else:
                    node.replace(existing, v)

        return PatchOperationBasicCounterResult(self, len(found))

    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        """Deserialize from an xml node"""
        xpath = ensure_xpath(node)
        if not isinstance(xpath, ElementXpath):
            raise MalformedPatchError("AddOrReplace only works on elements")

        value = ensure_value(node)

        return cls(
            xpath=xpath,
            value=value,
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

        node.append(self.value.copy())
