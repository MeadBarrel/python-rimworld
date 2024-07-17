""" Provides PatchOperationTest """

from dataclasses import dataclass
from typing import Self

from lxml import etree

from rimworld.patch.proto import PatchOperation, PatchOperationResult
from rimworld.patch.serializers import ensure_xpath
from rimworld.xml import Xpath


@dataclass(frozen=True)
class PatchOperationTestResult(PatchOperationResult):
    """Result of the PatchOperationTest patch operation"""

    operation: "PatchOperationTest"
    result: bool

    # pylint: disable-next=missing-function-docstring
    def is_successful(self) -> bool:
        return self.result

    # pylint: disable-next=missing-function-docstring
    def exception(
        self,
    ) -> Exception | None:
        return None

    # pylint: disable-next=missing-function-docstring
    def nodes_affected(self) -> int:
        return 0


@dataclass(frozen=True)
class PatchOperationTest(PatchOperation):
    """PatchOperationAdd

    https://rimworldwiki.com/wiki/Modding_Tutorials/PatchOperations#PatchOperationTest
    """

    xpath: Xpath

    def __call__(self, xml: etree._ElementTree, *_) -> PatchOperationResult:
        found = self.xpath.search(xml)
        return PatchOperationTestResult(self, bool(found))

    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        """Deserialize from an xml node"""
        return cls(
            xpath=ensure_xpath(node),
        )

    def to_xml(self, node: etree._Element):
        node.set("Class", "PatchOperationTest")

        xpath = etree.Element("xpath")
        xpath.text = self.xpath.xpath
        node.append(xpath)
