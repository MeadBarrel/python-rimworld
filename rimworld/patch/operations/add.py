from dataclasses import dataclass
from typing import Self
from lxml import etree

from rimworld.xml import ElementXpath

from .. import *


@dataclass(frozen=True, kw_only=True)
class PatchOperationAdd(PatchOperation):
    xpath: ElementXpath
    value: list[SafeElement]|str
    append: bool

    def apply(self, context: PatchContext) -> PatchOperationResult:
        found = self.xpath.search(context.xml)

        for elt in found:
            if self.append:
                if isinstance(self.value, str):
                    elt.text = (elt.text or '') + self.value
                else:
                    elt.extend([c.copy() for c in self.value])
            else:
                if isinstance(self.value, str):
                    elt.text = self.value + (elt.text or '')
                else:
                    for v in self.value:
                        elt.insert(0, v.copy())

        return PatchOperationBasicCounterResult(self, len(found))


    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        xpath = get_xpath(node)
        if not isinstance(xpath, ElementXpath):
            raise MalformedPatchError('PatchOperationAdd only operates on elements')
        return cls(
                xpath=xpath,
                value=get_value(node),
                append=get_order_append(node, True),
                )

    def to_xml(self, node: etree._Element):
        node.set('Class', 'PatchOperationAdd')

        xpath = etree.Element('xpath')
        xpath.text = self.xpath.xpath
        node.append(xpath)

        value = etree.Element('value')
        if isinstance(self.value, str):
            value.text = self.value
        else:
            value.extend([v.copy() for v in self.value])
        node.append(value)

        if not self.append:
            append = etree.Element('order')
            append.text = 'Prepend'
            node.append(append)


