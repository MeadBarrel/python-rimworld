from dataclasses import dataclass
from typing import Self
from lxml import etree

from rimworld.xml import ElementXpath

from .. import *


@dataclass(frozen=True)
class PatchOperationAttributeRemove(PatchOperation):
    xpath: ElementXpath
    attribute: str

    def apply(self, context: PatchContext) -> PatchOperationResult:
        found = self.xpath.search(context.xml)

        for elt in found:
            elt.attrib.pop(self.attribute)

        return PatchOperationBasicCounterResult(self, len(found))

    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        xpath = get_xpath(node)
        if not isinstance(xpath, ElementXpath):
            raise MalformedPatchError('AttributeRemove only works on elements')
        return cls(
                xpath=xpath,
                attribute=get_text(node, 'attribute'),
                )

