""" Provides PatchOperationAttributeSet """

from dataclasses import dataclass
from typing import Self

from lxml import etree

from rimworld.error import NoNodesFound
from rimworld.patch.proto import PatchOperation, PatchOperationResult
from rimworld.patch.result import (PatchOperationBasicCounterResult,
                                   PatchOperationFailedResult)
from rimworld.patch.serializers import ensure_xpath_elt
from rimworld.xml import ElementXpath, ensure_element_text


@dataclass(frozen=True)
class PatchOperationAttributeSet(PatchOperation):
    """PatchOperationAttributeSet

    https://rimworldwiki.com/wiki/Modding_Tutorials/PatchOperations#PatchOperationAttributeSet
    """

    xpath: ElementXpath
    attribute: str
    value: str

    def __call__(self, xml: etree._ElementTree, *_) -> PatchOperationResult:
        found = self.xpath.search(xml)

        if not found:
            return PatchOperationFailedResult(self, NoNodesFound(str(self.xpath)))

        for elt in found:
            elt.set(self.attribute, self.value)

        return PatchOperationBasicCounterResult(self, len(found))

    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        """Deserialize from an xml node"""
        xpath = ensure_xpath_elt(node)
        return cls(
            xpath=xpath,
            attribute=ensure_element_text(node.find("attribute")),
            value=ensure_element_text(node.find("value")),
        )

    def to_xml(self, node: etree._Element):
        node.set("Class", "PatchOperationAttributeSet")

        xpath = etree.Element("xpath")
        xpath.text = self.xpath.xpath
        node.append(xpath)

        attribute = etree.Element("attribute")
        attribute.text = self.attribute
        node.append(attribute)

        value = etree.Element("value")
        value.text = self.value
        node.append(value)
