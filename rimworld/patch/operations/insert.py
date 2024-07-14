from dataclasses import dataclass
from typing import Self
from lxml import etree

from rimworld.xml import ElementXpath

from .. import *


@dataclass(frozen=True)
class PatchOperationInsert(PatchOperation):
    xpath: ElementXpath
    value: list[SafeElement]
    append: bool

    def apply(self, context: PatchContext) -> PatchOperationResult:
        found = self.xpath.search(context.xml)
        if self.append:
            for f in found:
                for v in reversed(self.value):
                    f.addnext(v.copy())
        else:
            for f in found:
                for v in self.value:
                    f.addprevious(v.copy())

        return PatchOperationBasicCounterResult(self, len(found))

    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        xpath = get_xpath(node)
        if not isinstance(xpath, ElementXpath):
            raise MalformedPatchError('Insert only works on elements')
        return cls(
                xpath=xpath, 
                value=get_value_elt(node), 
                append=get_order_append(node, False),
                )

    def to_xml(self, node: etree._Element):
        node.set('Class', 'PatchOperationInsert')

        xpath = etree.Element('xpath')
        xpath.text = self.xpath.xpath
        node.append(xpath)

        value = etree.Element('value')
        if isinstance(self.value, str):
            value.text = self.value
        else:
            value.extend([v.copy() for v in self.value])
        node.append(value)

        if self.append:
            append = etree.Element('append')
            append.text = 'Append'
            node.append(append)


