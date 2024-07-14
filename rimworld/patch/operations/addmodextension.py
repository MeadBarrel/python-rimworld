from dataclasses import dataclass
from typing import Self
from lxml import etree

from rimworld.xml import ElementXpath

from .. import *


@dataclass(frozen=True, kw_only=True)
class PatchOperationAddModExtension(PatchOperation):
    xpath: ElementXpath
    value: list[SafeElement]

    def apply(self, context: PatchContext) -> PatchOperationResult:
        found = self.xpath.search(context.xml)

        for elt in found:
            mod_extensions = elt.find('modExtensions')
            if mod_extensions is None:
                mod_extensions = etree.Element('modExtensions')
                elt.append(mod_extensions)
            for v in self.value:
                mod_extensions.append(v.copy())

        return PatchOperationBasicCounterResult(self, len(found))

    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        xpath = get_xpath(node)
        if not isinstance(xpath, ElementXpath):
            raise MalformedPatchError('AddModExtension only operates on elements')
        return cls(
                xpath=xpath,
                value=get_value_elt(node),
                )

    def to_xml(self, node: etree._Element):
        node.set('Class', 'PatchOperationAddModExtension')

        xpath = etree.Element('xpath')
        xpath.text = self.xpath.xpath
        node.append(xpath)

        value = etree.Element('value')
        value.extend([v.copy() for v in self.value])
        node.append(value)


