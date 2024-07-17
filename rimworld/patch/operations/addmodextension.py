""" Provides PatchOperationAddModExtension """

from dataclasses import dataclass
from typing import Self

from lxml import etree

from rimworld.error import MalformedPatchError, NoNodesFound
from rimworld.patch.proto import PatchOperation, PatchOperationResult
from rimworld.patch.result import (PatchOperationBasicCounterResult,
                                   PatchOperationFailedResult)
from rimworld.patch.serializers import (SafeElement, ensure_value,
                                        ensure_xpath_elt)
from rimworld.xml import ElementXpath


@dataclass(frozen=True, kw_only=True)
class PatchOperationAddModExtension(PatchOperation):
    """PatchOperationAddModExtension

    https://rimworldwiki.com/wiki/Modding_Tutorials/PatchOperations#PatchOperationAddModExtension
    """

    xpath: ElementXpath
    value: SafeElement

    def __call__(self, xml: etree._ElementTree, *_) -> PatchOperationResult:
        found = self.xpath.search(xml)

        if not found:
            return PatchOperationFailedResult(self, NoNodesFound(str(self.xpath)))

        for elt in found:
            mod_extensions = elt.find("modExtensions")
            if mod_extensions is None:
                mod_extensions = etree.Element("modExtensions")
                elt.append(mod_extensions)
            for v in self.value.copy():
                mod_extensions.append(v)

        return PatchOperationBasicCounterResult(self, len(found))

    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        """Deserialize from an xml node"""
        xpath = ensure_xpath_elt(node)
        if not isinstance(xpath, ElementXpath):
            raise MalformedPatchError("AddModExtension only operates on elements")
        return cls(
            xpath=xpath,
            value=ensure_value(node),
        )

    def to_xml(self, node: etree._Element):
        node.set("Class", "PatchOperationAddModExtension")

        xpath = etree.Element("xpath")
        xpath.text = self.xpath.xpath
        node.append(xpath)
        node.append(self.value.copy())
