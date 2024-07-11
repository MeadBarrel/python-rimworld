from dataclasses import dataclass
from typing import Self
from lxml import etree

from ._base import *
from ._result import PatchOperationBasicCounterResult


@dataclass(frozen=True)
class PatchOperationSetName(PatchOperation):
    xpath: str
    name: str

    def apply(self, xml: etree._ElementTree, patcher: Patcher) -> PatchOperationBasicCounterResult:
        found = xpath_elements(xml, self.xpath)

        for elt in found:
            elt.tag = self.name

        return PatchOperationBasicCounterResult(self, len(found))

    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        xpath = get_xpath(node)
        name = get_text(node, 'name')
        return cls(
                PatchOperationMeta.from_xml(node),
                xpath, 
                name
                )
