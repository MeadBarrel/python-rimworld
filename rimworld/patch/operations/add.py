""" Provides PatchOperationAdd """

from dataclasses import dataclass
from typing import Self

from lxml import etree

from rimworld.error import NoNodesFound
from rimworld.patch.proto import PatchOperation, PatchOperationResult
from rimworld.patch.result import (PatchOperationBasicCounterResult,
                                   PatchOperationFailedResult)
from rimworld.patch.serializers import (Order, SafeElement, ensure_value,
                                        ensure_xpath_elt, get_order)
from rimworld.xml import ElementXpath


@dataclass(frozen=True)
class PatchOperationAdd(PatchOperation):
    """PatchOperationAdd

    https://rimworldwiki.com/wiki/Modding_Tutorials/PatchOperations#PatchOperationAdd
    """

    xpath: ElementXpath
    value: SafeElement
    order: Order = Order.APPEND

    def __call__(self, xml: etree._ElementTree, *_) -> PatchOperationResult:

        found = self.xpath.search(xml)

        if len(found) == 0:
            return PatchOperationFailedResult(self, NoNodesFound(str(self.xpath)))

        for elt in found:
            value = self.value.copy()
            match self.order:
                case Order.APPEND:
                    if value.text:
                        elt.text = (elt.text or "") + value.text
                    elt.extend(value)
                case Order.PREPEND:
                    if value.text:
                        elt.text = value.text + (elt.text or "")
                    for v in value:
                        elt.insert(0, v)

        return PatchOperationBasicCounterResult(self, len(found))

    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        """deserialize from xml"""
        return cls(
            xpath=ensure_xpath_elt(node),
            value=ensure_value(node),
            order=get_order(node, default=Order.APPEND),
        )

    def to_xml(self, node: etree._Element):
        node.set("Class", "PatchOperationAdd")

        xpath = etree.Element("xpath")
        xpath.text = self.xpath.xpath
        node.append(xpath)

        node.append(self.value.copy())

        if self.order != Order.APPEND:
            append = etree.Element("order")
            append.text = "Prepend"
            node.append(append)
