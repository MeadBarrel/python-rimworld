from dataclasses import dataclass
from enum import Enum, auto
from typing import Self
from lxml import etree
from rimworld.xml import ElementXpath
from ..proto import PatchContext, PatchOperation
from ..result import PatchOperationBasicCounterResult
from .._base import *
from ._base import *



@dataclass(frozen=True)
class PatchOperationSafeAdd(PatchOperation):
    xpath: ElementXpath
    value: list[SafeElement]
    safety_depth: int = -1
    compare: Compare = Compare.Name
    check_attributes: bool = False


    def apply(self, context: PatchContext) -> PatchOperationBasicCounterResult:
        found = self.xpath.search(context.xml)

        for node in found:
            for value in self.value:
                self._apply_recursive(node, value.copy(), self.safety_depth)

        return PatchOperationBasicCounterResult(self, len(found))

    def _apply_recursive(self, node: etree._Element, value: etree._Element, depth: int):
        existing = get_existing_node(self.compare, node, value)

        if self.check_attributes:
            if set(node.attrib.items()) != set(value.attrib.items()):
                existing = None


        if existing is None:
            node.append(value)
            return

        if depth == 1:
            return 

        for sub_value in value:
            self._apply_recursive(existing, sub_value, depth-1)


    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        xpath = get_xpath(node)
        if not isinstance(xpath, ElementXpath):
            raise MalformedPatchError('SafeAdd only works on elements')

        value = get_value_elt(node)

        return cls(
                xpath=xpath,
                value=value,
                safety_depth=get_safety_depth(node),
                compare=get_compare(node),
                check_attributes=get_check_attributes(node),
                )

