from dataclasses import dataclass
from typing import Self
from lxml import etree

from rimworld.xml import ElementXpath

from .. import *


@dataclass(frozen=True)
class PatchOperationSetName(PatchOperation):
    xpath: ElementXpath 
    name: str

    def apply(self, context: PatchContext) -> PatchOperationResult:
        found = self.xpath.search(context.xml)

        for elt in found:
            elt.tag = self.name

        return PatchOperationBasicCounterResult(self, len(found))

    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        xpath = get_xpath(node)
        if not isinstance(xpath, ElementXpath):
            raise MalformedPatchError('SetName only works on elements')
        return cls(
                xpath=xpath,
                name=get_text(node, 'name'),
                )

    def to_xml(self, node: etree._Element):
        node.set('Class', 'PatchOperationSetName')

        xpath = etree.Element('xpath')
        xpath.text = self.xpath.xpath
        node.append(xpath)

        name = etree.Element('name')
        name.text = self.name
        node.append(name)
