from dataclasses import dataclass
from enum import Enum, auto
from typing import Self
from lxml import etree
from rimworld.xml import ElementXpath
from ..proto import PatchContext, PatchOperation
from ..result import PatchOperationBasicCounterResult
from .._base import *


class SafeAddCompare(Enum):
    Name = auto()
    InnerText = auto()
    Both = auto()


@dataclass(frozen=True)
class PatchOperationSafeAdd(PatchOperation):
    xpath: ElementXpath
    value: list[SafeElement]
    safety_depth: int = -1
    compare: SafeAddCompare = SafeAddCompare.Name
    check_attributes: bool = False


    def apply(self, context: PatchContext) -> PatchOperationBasicCounterResult:
        found = self.xpath.search(context.xml)

        for node in found:
            for value in self.value:
                self._apply_recursive(node, value.copy(), self.safety_depth)

        return PatchOperationBasicCounterResult(self, len(found))

    def _apply_recursive(self, node: etree._Element, value: etree._Element, depth: int):
        existing = self._get_existing_node(node, value)

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


    def _get_existing_node(self, node: etree._Element, value: etree._Element) -> etree._Element|None:
        match self.compare:
            case SafeAddCompare.Name:
                if (n := node.find(value.tag)) is not None:
                    return n
            case SafeAddCompare.InnerText:
                for n in node:
                    if n.text == value.text:
                        return n
            case SafeAddCompare.Both:
                if (n:=node.find(value.tag)) is not None and n.text == value.text:
                    return n


    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        xpath = get_xpath(node)
        if not isinstance(xpath, ElementXpath):
            raise MalformedPatchError('SafeAdd only works on elements')

        safety_depth = -1
        if (n := node.find('safetyDepth')) is not None:
            if not n.text:
                raise MalformedPatchError('incorrect safetyDepth')
            try:
                safety_depth = int(n.text)
            except ValueError:
                raise MalformedPatchError('incorrect safetyDepth')

        match node.find('compare'):
            case None:
                compare = SafeAddCompare.Name
            case etree._Element(text="Name"):
                compare = SafeAddCompare.Name
            case etree._Element(text="InnerText"):
                compare = SafeAddCompare.InnerText
            case etree._Element(text="Both"):
                compare = SafeAddCompare.Both
            case _:
                raise MalformedPatchError(f'Incorrect compare value')

        match node.find('checkAttributes'):
            case None:
                check_attributes = False
            case etree._Element(text='false'):
                check_attributes = False
            case etree._Element(text='true'):
                check_attributes = True
            case _:
                raise MalformedPatchError(f'Incorrect checkAttributes value')

        value = get_value_elt(node)

        return cls(
                xpath=xpath,
                value=value,
                safety_depth=safety_depth,
                compare=compare,
                check_attributes=check_attributes,
                )

