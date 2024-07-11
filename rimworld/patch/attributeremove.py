from dataclasses import dataclass
from typing import Self
from lxml import etree

from ._base import *
from ._result import PatchOperationBasicCounterResult


@dataclass(frozen=True)
class PatchOperationAttributeRemove(PatchOperation):
    xpath: str
    attribute: str

    def apply(
            self, 
            xml: etree._ElementTree, 
            *_,
            ) -> PatchOperationBasicCounterResult:
        found = xpath_elements(xml, self.xpath)

        for elt in found:
            elt.attrib.pop(self.attribute)

        return PatchOperationBasicCounterResult(self, len(found))

    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        xpath = get_xpath(node)
        attribute = get_text(node, 'attribute')
        return cls(
                PatchOperationMeta.from_xml(node),
                xpath, 
                attribute
                )

