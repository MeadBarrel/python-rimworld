from dataclasses import dataclass
from rimworld.base import PatchOperationBase, PatchOperationResult


@dataclass(frozen=True)
class PatchOperationBasicCounterResult(PatchOperationResult):
    operation: PatchOperationBase
    _nodes_affected: int

    def is_successful(self) -> bool:
        return bool(self.nodes_affected)

    def nodes_affected(self) -> int:
        return self._nodes_affected

    def exception(self) -> Exception | None:
        return None


@dataclass(frozen=True)
class PatchOperationBasicConditionalResult(PatchOperationResult):
    operation: PatchOperationBase
    matched: bool
    child_result: PatchOperationResult|None

    def is_successful(self) -> bool:
        if not self.child_result:
            return False
        return self.child_result.is_successful()

    def nodes_affected(self) -> int:
        if self.child_result is None:
            return 0
        return self.child_result.nodes_affected()

    def exception(self) -> Exception | None:
        if self.child_result is None:
            return None
        return self.child_result.exception()


