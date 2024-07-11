from dataclasses import dataclass
from typing import Self
from lxml import etree

from ._base import *
from ._result import PatchOperationBasicCounterResult


@dataclass(frozen=True)
class PatchOperationAddModExtension(PatchOperation):
    xpath: str
    value: list[SafeElement]

    def apply(
            self, 
            xml: etree._ElementTree, 
            *_,
            ) -> PatchOperationBasicCounterResult:
        found = xpath_elements(xml, self.xpath)

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
        value = get_value(node)
        return cls(
                PatchOperationMeta.from_xml(node),
                xpath, 
                value,
                )

