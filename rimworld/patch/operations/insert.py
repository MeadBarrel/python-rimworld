""" Provides PatchOperationInsert """

from dataclasses import dataclass
from typing import Self

from lxml import etree

from rimworld.error import NoNodesFound, PatchError
from rimworld.patch.proto import PatchOperation, PatchOperationResult
from rimworld.patch.result import (PatchOperationBasicCounterResult,
                                   PatchOperationFailedResult)
from rimworld.patch.serializers import (Order, SafeElement, ensure_value,
                                        ensure_xpath_elt, get_order)
from rimworld.xml import ElementXpath


@dataclass(frozen=True)
class PatchOperationInsert(PatchOperation):
    """PatchOperationAdd

    https://rimworldwiki.com/wiki/Modding_Tutorials/PatchOperations#PatchOperationAdd
    """

    xpath: ElementXpath
    value: SafeElement
    order: Order = Order.PREPEND

    def __call__(self, xml: etree._ElementTree, *_) -> PatchOperationResult:

        found = self.xpath.search(xml)

        if not found:
            return PatchOperationFailedResult(self, NoNodesFound(str(self.xpath)))

        for node in found:
            value = self.value.copy()
            if value.text:
                raise PatchError("Value cannot be text")
            match self.order:
                case Order.APPEND:
                    for v in reversed(value):
                        node.addnext(v)
                case Order.PREPEND:
                    for v in value:
                        node.addprevious(v)

        return PatchOperationBasicCounterResult(self, len(found))

    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        """Deserialize from an xml node"""
        xpath = ensure_xpath_elt(node)
        return cls(
            xpath=xpath,
            value=ensure_value(node),
            order=get_order(node, default=Order.PREPEND),
        )

    def to_xml(self, node: etree._Element):
        node.set("Class", "PatchOperationInsert")

        xpath = etree.Element("xpath")
        xpath.text = self.xpath.xpath
        node.append(xpath)

        node.append(self.value.copy())

        if self.order == Order.APPEND:
            append = etree.Element("append")
            append.text = "Append"
            node.append(append)
