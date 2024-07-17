""" Provides PatchOperationRemove """

from dataclasses import dataclass
from typing import Self, cast

from lxml import etree

from rimworld.error import MalformedPatchError, NoNodesFound, PatchError
from rimworld.patch.proto import PatchOperation, PatchOperationResult
from rimworld.patch.result import (PatchOperationBasicCounterResult,
                                   PatchOperationFailedResult)
from rimworld.patch.serializers import ensure_xpath
from rimworld.xml import ElementXpath, TextXpath


@dataclass(frozen=True, kw_only=True)
class PatchOperationRemove(PatchOperation):
    """PatchOperationRemove

    https://rimworldwiki.com/wiki/Modding_Tutorials/PatchOperations#PatchOperationRemove
    """

    xpath: ElementXpath | TextXpath

    def __call__(self, xml: etree._ElementTree, *_) -> PatchOperationResult:

        match self.xpath:
            case ElementXpath():
                found = self.xpath.search(xml)
                if not found:
                    return PatchOperationFailedResult(
                        self, NoNodesFound(str(self.xpath))
                    )
                for elt in found:
                    parent = elt.getparent()
                    if parent is None:
                        raise PatchError(f"Parent not found for {self.xpath}")
                    parent.remove(elt)
            case TextXpath():
                found = self.xpath.search(xml)
                if not found:
                    return PatchOperationFailedResult(
                        self, NoNodesFound(str(self.xpath))
                    )
                for elt in found:
                    elt.node.text = None

        return PatchOperationBasicCounterResult(self, len(found))

    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        """Deserialize from an xml node"""
        xpath = ensure_xpath(node)
        if type(xpath) not in (ElementXpath, TextXpath):
            raise MalformedPatchError("Remove only works on texts or elements")
        return cls(xpath=cast(ElementXpath | TextXpath, xpath))

    def to_xml(self, node: etree._Element):
        node.set("Class", "PatchOperationRemove")

        xpath = etree.Element("xpath")
        xpath.text = self.xpath.xpath
        node.append(xpath)
