from dataclasses import dataclass
from typing import Self, cast
from lxml import etree
from ._base import *


@dataclass(frozen=True)
class PatchOperationSequenceResult(PatchOperationResult):
    operation: 'PatchOperationSequence'
    results: list[PatchOperationResult]

    def is_successful(self) -> bool:
        return bool(self.results)

    def exception(self) -> Exception | None:
        exceptions = [r.exception() for r in self.results if r.exception() is not None]
        if exceptions:
            return ExceptionGroup(
                    'Patch operation sequence errors', 
                    cast(list[Exception], exceptions)
                    )

    def count_nodes_affected(self) -> int:
        return sum(r.count_nodes_affected() for r in self.results)



@dataclass(frozen=True)
class PatchOperationSequence(PatchOperation):

    operations: list[PatchOperation]

    def apply(self, xml: etree._ElementTree, patcher: Patcher) -> PatchOperationSequenceResult:
        results = []
        for operation in self.operations:
            operation_result = patcher.apply(xml, operation)
            results.append(operation_result)
            if not operation_result.is_successful:
                break
        return PatchOperationSequenceResult(self, results)

    @classmethod
    def from_xml(cls, node: etree._Element, patcher: Patcher) -> Self:

        operations = patcher.collect_patches(
                get_element(node, 'operations'),
                tag='li',
                )
        return cls(
                PatchOperationMeta.from_xml(node),
                operations
                )
