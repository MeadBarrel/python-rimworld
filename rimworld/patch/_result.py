from ._base import PatchOperationResult, PatchOperation
from dataclasses import dataclass


@dataclass(frozen=True)
class PatchOperationBasicCounterResult(PatchOperationResult):
    operation: PatchOperation
    nodes_affected: int

    def is_successful(self) -> bool:
        return bool(self.nodes_affected)

    def count_nodes_affected(self) -> int:
        return self.nodes_affected

    def exception(self) -> Exception | None:
        return None


@dataclass(frozen=True)
class PatchOperationBasicConditionalResult(PatchOperationResult):
    operation: PatchOperation
    matched: bool
    child_result: PatchOperationResult|None

    def is_successful(self) -> bool:
        if not self.child_result:
            return False
        return self.child_result.is_successful()

    def count_nodes_affected(self) -> int:
        if self.child_result is None:
            return 0
        return self.child_result.count_nodes_affected()

    def exception(self) -> Exception | None:
        if self.child_result is None:
            return None
        return self.child_result.exception()


@dataclass(frozen=True)
class PatchOperationMetaResult(PatchOperationResult):
    pass


@dataclass(frozen=True)
class PatchOperationSuppressed(PatchOperationMetaResult):
    child: PatchOperationResult
    
    def is_successful(self) -> bool:
        return True

    def exception(self) -> Exception|None:
        return self.child.exception()

    def count_nodes_affected(self) -> int:
        return self.child.count_nodes_affected()




@dataclass(frozen=True)
class PatchOperationInverted(PatchOperationMetaResult):
    child: PatchOperationResult

    def is_successful(self) -> bool:
        return not self.child.is_successful()

    def exception(self) -> Exception|None:
        return self.child.exception()

    def count_nodes_affected(self) -> int:
        return self.child.count_nodes_affected()



@dataclass(frozen=True)
class PatchOperationDenied(PatchOperationMetaResult):
    operation: PatchOperation

    def is_successful(self) -> bool:
        return False

    def exception(self) -> Exception|None:
        return None

    def count_nodes_affected(self) -> int:
        return 0


@dataclass(frozen=True)
class PatchOperationFailure(PatchOperationMetaResult):
    operation: PatchOperation
    error: Exception

    def is_successful(self) -> bool:
        return False

    def exception(self) -> Exception:
        return self.error

    def count_nodes_affected(self) -> int:
        return 0
