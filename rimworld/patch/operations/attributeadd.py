""" Provides PatchOperationAttributeAdd """

from dataclasses import dataclass
from typing import Self

from lxml import etree

from rimworld.error import NoNodesFound
from rimworld.patch.proto import PatchOperation, PatchOperationResult
from rimworld.patch.result import (PatchOperationBasicCounterResult,
                                   PatchOperationFailedResult)
from rimworld.patch.serializers import ensure_xpath_elt
from rimworld.xml import ElementXpath, ensure_element_text


@dataclass(frozen=True, kw_only=True)
class PatchOperationAttributeAdd(PatchOperation):
    """PatchOperationAttributeAdd

    https://rimworldwiki.com/wiki/Modding_Tutorials/PatchOperations#PatchOperationAttributeAdd
    """

    xpath: ElementXpath
    attribute: str
    value: str

    def __call__(self, xml: etree._ElementTree, *_) -> PatchOperationResult:
        found = self.xpath.search(xml)
        if not found:
            return PatchOperationFailedResult(self, NoNodesFound(str(self.xpath)))

        for elt in found:
            if elt.get(self.attribute) is not None:
                continue
            elt.set(self.attribute, self.value)
        return PatchOperationBasicCounterResult(self, len(found))

    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        """Deserialize the operation from an xml node"""
        xpath = ensure_xpath_elt(node)
        return cls(
            xpath=xpath,
            attribute=ensure_element_text(node.find("attribute")),
            value=ensure_element_text(node.find("value")),
        )

    def to_xml(self, node: etree._Element):
        node.set("Class", "PatchOperationAttributeAdd")

        xpath = etree.Element("xpath")
        xpath.text = self.xpath.xpath
        node.append(xpath)

        attribute = etree.Element("attribute")
        attribute.text = self.attribute
        node.append(attribute)

        value = etree.Element("value")
        value.text = self.value
        node.append(value)
