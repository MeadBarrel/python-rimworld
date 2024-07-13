from dataclasses import dataclass
from typing import Self
from lxml import etree

from rimworld.xml import ElementXpath

from .. import *


@dataclass(frozen=True, kw_only=True)
class PatchOperationAttributeAdd(PatchOperation):
    xpath: ElementXpath
    attribute: str
    value: str

    def apply(self, context: PatchContext) -> PatchOperationResult:
        found = self.xpath.search(context.xml)

        for elt in found:
            if elt.get(self.attribute) is not None:
                continue
            elt.set(self.attribute, self.value)
        return PatchOperationBasicCounterResult(self, len(found))

    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        xpath = get_xpath(node)
        if not isinstance(xpath, ElementXpath):
            raise MalformedPatchError('AttributeAdd only works on elements')
        return cls(
                xpath=xpath,
                attribute=get_text(node, 'attribute'),
                value=get_text(node, 'value'),
                )
