from dataclasses import dataclass
from typing import Self, cast
from lxml import etree

from .. import *


@dataclass(frozen=True)
class PatchOperationSequenceResult(PatchOperationResult):
    operation: 'PatchOperationSequence'
    results: list[PatchOperationResult]

    def is_successful(self) -> bool:
        return bool(self.results)

    def exception(self) -> Exception | None:
        exceptions = [r.exception for r in self.results if r.exception is not None]
        if exceptions:
            return ExceptionGroup(
                    'Patch operation sequence errors', 
                    cast(list[Exception], exceptions)
                    )

    def nodes_affected(self) -> int:
        return sum(r.nodes_affected for r in self.results)



@dataclass(frozen=True, kw_only=True)
class PatchOperationSequence(PatchOperation):

    operations: list[PatchOperation]

    def apply(self, context: PatchContext) -> PatchOperationResult:
        results = []
        for operation in self.operations:
            operation_result = context.apply_operation(operation)
            results.append(operation_result)
            if not operation_result.is_successful:
                break
        return PatchOperationSequenceResult(self, results)

    @classmethod
    def from_xml(cls, patcher: Patcher, node: etree._Element) -> Self:

        operations = patcher.collect_operations(
                get_element(node, 'operations'),
                tag='li',
                )
        return cls(
                operations=operations,
                )
