""" Provides PatchOperationConditional """

from dataclasses import dataclass
from typing import Self

from lxml import etree

from rimworld.patch.proto import (PatchContext, Patcher, PatchOperation,
                                  PatchOperationResult)
from rimworld.patch.result import PatchOperationBasicConditionalResult
from rimworld.patch.serializers import ensure_xpath
from rimworld.xml import Xpath, make_element


@dataclass(frozen=True)
class PatchOperationConditional(PatchOperation):
    """PatchOperationAdd

    https://rimworldwiki.com/wiki/Modding_Tutorials/PatchOperations#PatchOperationConditional
    """

    xpath: Xpath
    match: PatchOperation | None
    nomatch: PatchOperation | None

    def __call__(
        self, xml: etree._ElementTree, context: PatchContext
    ) -> PatchOperationResult:
        matches = self.xpath.search(xml)
        if matches:
            return PatchOperationBasicConditionalResult(
                self, True, self.match(xml, context) if self.match else None
            )
        return PatchOperationBasicConditionalResult(
            self, False, self.nomatch(xml, context) if self.nomatch else None
        )

    @classmethod
    def from_xml(cls, get_operation: Patcher, node: etree._Element) -> Self:
        """Deserialize from an xml node"""
        match_elt = node.find("match")
        match = get_operation(match_elt) if match_elt is not None else None

        nomatch_elt = node.find("nomatch")
        nomatch = get_operation(nomatch_elt) if nomatch_elt is not None else None

        return cls(
            xpath=ensure_xpath(node),
            match=match,
            nomatch=nomatch,
        )

    def to_xml(self, node: etree._Element):
        node.set("Class", "PatchOperationConditional")

        make_element("xpath", str(self.xpath), parent=node)

        if self.match is not None:
            match = etree.Element("match")
            self.match.to_xml(match)
            node.append(match)
        if self.nomatch is not None:
            nomatch = etree.Element("nomatch")
            self.nomatch.to_xml(nomatch)
            node.append(nomatch)
