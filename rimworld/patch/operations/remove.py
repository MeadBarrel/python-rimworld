from dataclasses import dataclass
from typing import Self, cast
from lxml import etree

from rimworld.xml import ElementXpath, TextXpath

from .. import *


@dataclass(frozen=True, kw_only=True)
class PatchOperationRemove(PatchOperation):
    xpath: ElementXpath|TextXpath

    def apply(self, context: PatchContext) -> PatchOperationResult:

        match self.xpath:
            case ElementXpath():
                found = self.xpath.search(context.xml)
                for elt in found:
                    parent = elt.getparent()
                    if parent is None:
                        raise PatchError(f'Parent not found for {self.xpath}')
                    parent.remove(elt)
            case TextXpath():
                found = self.xpath.search(context.xml)
                for elt in found:
                    elt.node.text = None

        return PatchOperationBasicCounterResult(self, len(found))

    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        xpath = get_xpath(node)
        if type(xpath) not in (ElementXpath, TextXpath):
            raise MalformedPatchError('Remove only works on texts or elements')
        return cls(
                xpath=cast(ElementXpath|TextXpath, xpath)
                )
