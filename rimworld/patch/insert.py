from dataclasses import dataclass
from typing import Self
from lxml import etree

from rimworld.base import *
from ._base import *
from ._result import PatchOperationBasicCounterResult


@dataclass(frozen=True)
class PatchOperationInsert(PatchOperation):
    xpath: str
    value: list[SafeElement]
    append: bool

    def _apply(self, world: World) -> PatchOperationBasicCounterResult:
        found = xpath_elements(world, self.xpath)
        if self.append:
            for f in found:
                for v in reversed(self.value):
                    f.addnext(v.copy())
        else:
            for f in found:
                for v in self.value:
                    f.addprevious(v.copy())

        return PatchOperationBasicCounterResult(self, len(found))

    @classmethod
    def from_xml(cls, world: World, node: etree._Element) -> Self:
        unused(world)
        xpath = get_xpath(node)
        value = get_value(node)
        append = get_order_append(node, False)
        return cls(
                PatchOperationMeta.from_xml(node),
                xpath, 
                value, 
                append
                )
