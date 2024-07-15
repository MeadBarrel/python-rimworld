from dataclasses import dataclass

from rimworld.xml import ElementXpath

from ..proto import *
from .._base import *
from ..result import PatchOperationBasicCounterResult
from ._base import *


@dataclass(frozen=True)
class PatchOperationAddOrReplace(PatchOperation):
    xpath: ElementXpath
    compare: Compare
    check_attributes: bool
    value: list[SafeElement]

    def apply(self, context: PatchContext) -> PatchOperationBasicCounterResult:
        found = self.xpath.search(context.xml)

        for node in found:
            for value in self.value:
                v = value.copy()
                existing = get_existing_node(self.compare, node, v)
                if existing is None:
                    node.append(v)
                else:
                    node.replace(existing, v)

        return PatchOperationBasicCounterResult(self, len(found))


    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        xpath = get_xpath(node)
        if not isinstance(xpath, ElementXpath):
            raise MalformedPatchError('AddOrReplace only works on elements')

        value = get_value_elt(node)

        return cls(
                xpath=xpath,
                value=value,
                compare=get_compare(node),
                check_attributes=get_check_attributes(node),
                )

    def to_xml(self, node: etree._Element):
        node.set('Class', 'PatchOperationAdd')

        xpath = etree.Element('xpath')
        xpath.text = self.xpath.xpath
        node.append(xpath)

        set_compare(node, self.compare)
        set_check_attributes(node, self.check_attributes)

        value = etree.Element('value')
        value.extend([v.copy() for v in self.value])
        node.append(value)

