from dataclasses import dataclass
from typing import Self
from lxml import etree

from ._base import *
from ._result import PatchOperationBasicCounterResult


@dataclass(frozen=True)
class PatchOperationAttributeSet(PatchOperation):
    xpath: str
    attribute: str
    value: str

    def apply(
            self, 
            xml: etree._ElementTree, 
            *_,
            ) -> PatchOperationBasicCounterResult:
        found = xpath_elements(xml, self.xpath)

        for elt in found:
            elt.set(self.attribute, self.value)

        return PatchOperationBasicCounterResult(self, len(found))

    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        xpath = get_xpath(node)
        attribute = get_text(node, 'attribute')
        value = get_text(node, 'value')
        return cls(
                PatchOperationMeta.from_xml(node),
                xpath, 
                attribute, 
                value
                )
