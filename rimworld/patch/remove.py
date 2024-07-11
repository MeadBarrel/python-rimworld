from dataclasses import dataclass
from typing import Self
from lxml import etree
from ._base import *
from ._result import PatchOperationBasicCounterResult



@dataclass(frozen=True)
class PatchOperationRemove(PatchOperation):
    xpath: str

    def apply(
            self, 
            xml: etree._ElementTree, 
            *_,
            ) -> PatchOperationResult:
        found = xpath_elements(xml, self.xpath)
        for elt in found:
            parent = elt.getparent()
            if parent is None:
                raise PatchError(f'Parent not found for {self.xpath}')
            parent.remove(elt)
        return PatchOperationBasicCounterResult(self, len(found))

    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        xpath = get_xpath(node)
        return cls(PatchOperationMeta.from_xml(node), xpath)
