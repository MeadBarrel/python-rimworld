from dataclasses import dataclass
from typing import Self
from lxml import etree

from rimworld.base import *
from ._base import *
from ._result import PatchOperationBasicCounterResult


@dataclass(frozen=True)
class PatchOperationAttributeRemove(PatchOperation):
    xpath: str
    attribute: str

    def _apply(self, world: World) -> PatchOperationBasicCounterResult:
        found = xpath_elements(world, self.xpath)

        for elt in found:
            elt.attrib.pop(self.attribute)

        return PatchOperationBasicCounterResult(self, len(found))

    @classmethod
    def from_xml(cls, world: World, node: etree._Element) -> Self:
        unused(world)
        xpath = get_xpath(node)
        attribute = get_text(node, 'attribute')
        return cls(
                PatchOperationMeta.from_xml(node),
                xpath, 
                attribute
                )

