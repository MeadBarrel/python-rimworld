""" Provides PatchOperationSetName"""

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
class PatchOperationSetName(PatchOperation):
    """PatchOperationSetName

    https://rimworldwiki.com/wiki/Modding_Tutorials/PatchOperations#PatchOperationSetName
    """

    xpath: ElementXpath
    name: str

    def __call__(self, xml: etree._ElementTree, *_) -> PatchOperationResult:
        found = self.xpath.search(xml)
        if not found:
            return PatchOperationFailedResult(self, NoNodesFound(str(self.xpath)))

        for elt in found:
            elt.tag = self.name

        return PatchOperationBasicCounterResult(self, len(found))

    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        """Deserialize from an xml node"""
        xpath = ensure_xpath_elt(node)
        return cls(
            xpath=xpath,
            name=ensure_element_text(node.find("name")),
        )

    def to_xml(self, node: etree._Element):
        node.set("Class", "PatchOperationSetName")

        xpath = etree.Element("xpath")
        xpath.text = self.xpath.xpath
        node.append(xpath)

        name = etree.Element("name")
        name.text = self.name
        node.append(name)
