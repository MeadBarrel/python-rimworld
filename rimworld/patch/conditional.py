from dataclasses import dataclass
from typing import Self
from lxml import etree

from rimworld.rimworld import Rimworld
from ._base import *
from ._result import PatchOperationBasicConditionalResult


@dataclass(frozen=True)
class PatchOperationConditional(PatchOperation):
    xpath: str
    match: PatchOperation|None
    nomatch: PatchOperation|None

    def apply(
            self, 
            xml: etree._ElementTree, 
            patcher: Patcher,
            rimworld: Rimworld,
            ) -> PatchOperationBasicConditionalResult:
        matches = bool(xpath_elements(xml, self.xpath))
        if matches:
            return PatchOperationBasicConditionalResult(
                    self,
                    True,
                    patcher.apply(rimworld, xml, self.match) if self.match else None
                    )
        return PatchOperationBasicConditionalResult(
                self,
                False,
                patcher.apply(rimworld, xml, self.nomatch) if self.nomatch else None
                )

    @classmethod
    def from_xml(cls, node: etree._Element, patcher: Patcher) -> Self:
        xpath = get_xpath(node)
        match_elt = node.find('match')
        match = patcher.select_operation(match_elt) if match_elt is not None else None

        nomatch_elt = node.find('nomatch')
        nomatch = patcher.select_operation(nomatch_elt) if nomatch_elt is not None else None
        return cls(
                PatchOperationMeta.from_xml(node),
                xpath, 
                match, 
                nomatch
                )
