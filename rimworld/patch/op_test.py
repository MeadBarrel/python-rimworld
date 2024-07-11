from dataclasses import dataclass
from typing import Self
from lxml import etree
from ._base import *


@dataclass(frozen=True)
class PatchOperationTestResult(PatchOperationResult):
    operation: 'PatchOperationTest'
    result: bool

    def is_successful(self) -> bool:
        return self.result

    def exception(self) -> Exception | None:
        return None

    def count_nodes_affected(self) -> int:
        return 0


@dataclass(frozen=True)
class PatchOperationTest(PatchOperation):
    xpath: str

    def apply(self, xml: etree._ElementTree, patcher: Patcher) -> PatchOperationTestResult:
        found = xpath_elements(xml, self.xpath)
        return PatchOperationTestResult(self, bool(found))

    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        xpath = get_xpath(node)
        return cls(
                PatchOperationMeta.from_xml(node),
                xpath,
                )
