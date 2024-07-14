from dataclasses import dataclass
from typing import Self
from lxml import etree

from rimworld.xml import Xpath

from .. import *


@dataclass(frozen=True)
class PatchOperationTestResult(PatchOperationResult):
    operation: 'PatchOperationTest'
    result: bool

    def is_successful(self) -> bool:
        return self.result

    def exception(self) -> Exception | None:
        return None

    def nodes_affected(self) -> int:
        return 0


@dataclass(frozen=True)
class PatchOperationTest(PatchOperation):
    xpath: Xpath

    def apply(self, context: PatchContext) -> PatchOperationResult:
        found = self.xpath.search(context.xml)
        return PatchOperationTestResult(self, bool(found))

    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        return cls(
                xpath=get_xpath(node),
                )

    def to_xml(self, node: etree._Element):
        node.set('Class', 'PatchOperationTest')

        xpath = etree.Element('xpath')
        xpath.text = self.xpath.xpath
        node.append(xpath)

