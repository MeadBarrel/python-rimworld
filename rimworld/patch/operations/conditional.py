from dataclasses import dataclass
from typing import Self
from lxml import etree

from rimworld.xml import Xpath

from .. import *


@dataclass(frozen=True)
class PatchOperationConditional(PatchOperation):
    xpath: Xpath
    match: PatchOperation|None
    nomatch: PatchOperation|None

    def apply(self, context: PatchContext) -> PatchOperationResult:
        matches = self.xpath.search(context.xml)
        if matches:
            return PatchOperationBasicConditionalResult(
                    self,
                    True,
                    context.apply_operation(self.match) if self.match else None
                    )
        return PatchOperationBasicConditionalResult(
                self,
                False,
                context.apply_operation(self.nomatch) if self.nomatch else None
                )

    @classmethod
    def from_xml(cls, patcher: Patcher, node: etree._Element) -> Self:
        match_elt = node.find('match')
        match = patcher.select_operation(match_elt) if match_elt is not None else None

        nomatch_elt = node.find('nomatch')
        nomatch = patcher.select_operation(nomatch_elt) if nomatch_elt is not None else None

        return cls(
                xpath=get_xpath(node),
                match=match,
                nomatch=nomatch,
                )

    def to_xml(self, node: etree._Element):
        node.set('Class', 'PatchOperationConditional')

        if self.match is not None:
            match = etree.Element('match')
            self.match.to_xml(match)
            node.append(match)
        if self.nomatch is not None:
            nomatch = etree.Element('nomatch')
            self.nomatch.to_xml(nomatch)
            node.append(nomatch)

