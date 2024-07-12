from dataclasses import dataclass
from typing import Self
from lxml import etree

from rimworld.base import *
from ._base import *
from ._result import PatchOperationBasicConditionalResult


@dataclass(frozen=True)
class PatchOperationConditional(PatchOperation):
    xpath: str
    match: PatchOperation|None
    nomatch: PatchOperation|None

    def _apply(self, world: World) -> PatchOperationBasicConditionalResult:
        matches = bool(xpath_elements(world.xml, self.xpath))
        if matches:
            return PatchOperationBasicConditionalResult(
                    self,
                    True,
                    self.match.apply(world) if self.match else None
                    )
        return PatchOperationBasicConditionalResult(
                self,
                False,
                self.nomatch.apply(world) if self.nomatch else None
                )

    @classmethod
    def from_xml(cls, world: World, node: etree._Element) -> Self:
        xpath = get_xpath(node)
        match_elt = node.find('match')
        match = world.select_patch_operation(match_elt) if match_elt is not None else None

        nomatch_elt = node.find('nomatch')
        nomatch = world.select_patch_operation(nomatch_elt) if nomatch_elt is not None else None
        return cls(
                PatchOperationMeta.from_xml(node),
                xpath, 
                match, 
                nomatch
                )
