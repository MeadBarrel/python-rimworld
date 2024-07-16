""" Provides PatchOperationSequence """

from dataclasses import dataclass
from typing import Self, cast

from lxml import etree

from rimworld.patch.proto import (PatchContext, Patcher, PatchOperation,
                                  PatchOperationResult)
from rimworld.patch.serializers import ensure_element


@dataclass(frozen=True)
class PatchOperationSequenceResult(PatchOperationResult):
    """Result of a PatchOperationSequence operation"""

    operation: "PatchOperationSequence"
    results: list[PatchOperationResult]

    # pylint: disable-next=missing-function-docstring
    def is_successful(self) -> bool:
        return bool(self.results)

    # pylint: disable-next=missing-function-docstring
    def exception(self) -> Exception | None:
        exceptions = [r.exception for r in self.results if r.exception is not None]
        if exceptions:
            return ExceptionGroup(
                "Patch operation sequence errors", cast(list[Exception], exceptions)
            )
        return None

    # pylint: disable-next=missing-function-docstring
    def nodes_affected(self) -> int:
        return sum(r.nodes_affected for r in self.results)


@dataclass(frozen=True)
class PatchOperationSequence(PatchOperation):
    """PatchOperationSequence

    https://rimworldwiki.com/wiki/Modding_Tutorials/PatchOperations#PatchOperationSequence
    """

    operations: list[PatchOperation]

    def apply(self, patcher: Patcher, context: PatchContext) -> PatchOperationResult:
        results = []
        for operation in self.operations:
            operation_result = patcher.apply_operation(operation, context)
            results.append(operation_result)
            if not operation_result.is_successful:
                break
        return PatchOperationSequenceResult(self, results)

    @classmethod
    def from_xml(cls, patcher: Patcher, node: etree._Element) -> Self:
        """Deserialize from an xml node"""
        operations = patcher.collect_operations(
            ensure_element(node, "operations"),
            tag="li",
        )
        return cls(
            operations=operations,
        )

    def to_xml(self, node: etree._Element):
        node.set("Class", "PatchOperationSequence")

        operations = etree.Element("operations")
        for operation in self.operations:
            n = etree.Element("li")
            operation.to_xml(n)
        node.append(operations)
