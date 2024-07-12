from dataclasses import dataclass
from typing import Self
from lxml import etree

from rimworld.base import PatchOperation, World, unused, PatchOperationMeta
from ._result import PatchOperationBasicCounterResult
from ._base import *


@dataclass(frozen=True)
class PatchOperationAdd(PatchOperation):
    xpath: str
    value: list[SafeElement]
    append: bool

    def _apply(self, world: World) -> PatchOperationBasicCounterResult:
        found = xpath_elements(world.xml, self.xpath)

        if self.append:
            for elt in found:
                elt.extend([c.copy() for c in self.value])
        else:
            for elt in found:
                for v in self.value:
                    elt.insert(0, v.copy())
        return PatchOperationBasicCounterResult(self, len(found))

    @classmethod
    def from_xml(cls, world: World, node: etree._Element) -> Self:
        unused(world)
        xpath = get_xpath(node)
        value = get_value(node)
        append =get_order_append(node, True)

        return cls(
                PatchOperationMeta.from_xml(node), 
                xpath, 
                value, 
                append
                )

