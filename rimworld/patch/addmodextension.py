from dataclasses import dataclass
from typing import Self
from lxml import etree

from rimworld.base import *
from ._base import *
from ._result import PatchOperationBasicCounterResult


@dataclass(frozen=True)
class PatchOperationAddModExtension(PatchOperation):
    xpath: str
    value: list[SafeElement]

    def _apply(self, world: World) -> PatchOperationBasicCounterResult:
        found = xpath_elements(world, self.xpath)

        for elt in found:
            mod_extensions = elt.find('modExtensions')
            if mod_extensions is None:
                mod_extensions = etree.Element('modExtensions')
                elt.append(mod_extensions)
            for v in self.value:
                mod_extensions.append(v.copy())

        return PatchOperationBasicCounterResult(self, len(found))

    @classmethod
    def from_xml(cls, world: World, node: etree._Element) -> Self:
        unused(world)
        xpath = get_xpath(node)
        value = get_value(node)
        return cls(
                PatchOperationMeta.from_xml(node),
                xpath, 
                value,
                )

