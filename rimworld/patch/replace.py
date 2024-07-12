from dataclasses import dataclass
from typing import Self
from lxml import etree

from rimworld.base import *
from ._base import *
from ._result import PatchOperationBasicCounterResult


@dataclass(frozen=True)
class PatchOperationReplace(PatchOperation):
    xpath: str
    value: list[SafeElement]

    def _apply(self, world: World) -> PatchOperationBasicCounterResult:
        found = xpath_elements(world.xml, self.xpath)

        for f in found:
            parent = f.getparent()
            if parent is None:
                raise PatchError(f'Parent not found for {self.xpath}')
            v1, *v_ = self.value
            v1_ = v1.copy()
            parent.replace(f, v1_)

            for v in reversed(v_):
                v1_.addnext(v.copy())

        return PatchOperationBasicCounterResult(self, len(found))

    @classmethod
    def from_xml(cls, world: World, node: etree._Element) -> Self:
        unused(world)
        xpath = get_xpath(node)
        value = get_value(node)
        return cls(
                PatchOperationMeta.from_xml(node),
                xpath, 
                value
                )

