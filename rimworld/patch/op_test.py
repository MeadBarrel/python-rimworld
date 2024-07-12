from dataclasses import dataclass
from typing import Self
from lxml import etree

from rimworld.base import *
from ._base import *


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
    xpath: str

    def _apply(self, world: World) -> PatchOperationTestResult:
        found = xpath_elements(world, self.xpath)
        return PatchOperationTestResult(self, bool(found))

    @classmethod
    def from_xml(cls, world: World, node: etree._Element) -> Self:
        unused(world)
        xpath = get_xpath(node)
        return cls(
                PatchOperationMeta.from_xml(node),
                xpath,
                )
