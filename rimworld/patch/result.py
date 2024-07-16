""" Contains some common result classes for patch operations """

# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring

from dataclasses import dataclass

from .proto import PatchOperation, PatchOperationResult


@dataclass(frozen=True)
class PatchOperationFailedResult(PatchOperationResult):
    operation: PatchOperation
    exception: Exception

    @property
    def is_successful(self) -> bool:
        return False

    @property
    def nodes_affected(self) -> int:
        return 0


@dataclass(frozen=True)
class PatchOperationBasicCounterResult(PatchOperationResult):
    operation: PatchOperation
    nodes_affected: int

    @property
    def is_successful(self) -> bool:
        return bool(self.nodes_affected)

    @property
    def exception(self) -> None:
        return None


@dataclass(frozen=True)
class PatchOperationBasicConditionalResult(PatchOperationResult):
    operation: PatchOperation
    matched: bool
    child_result: PatchOperationResult | None

    @property
    def is_successful(self) -> bool:
        if not self.child_result:
            return False
        return self.child_result.is_successful

    @property
    def nodes_affected(self) -> int:
        if self.child_result is None:
            return 0
        return self.child_result.nodes_affected

    @property
    def exception(self) -> Exception | None:
        if self.child_result is None:
            return None
        return self.child_result.exception


@dataclass(frozen=True)
class PatchOperationSuppressed(PatchOperationResult):
    child: PatchOperationResult

    @property
    def is_successful(self) -> bool:
        return True

    @property
    def exception(self) -> Exception | None:
        return self.child.exception

    @property
    def nodes_affected(self) -> int:
        return self.child.nodes_affected

    @property
    def operation(self) -> PatchOperation:
        return self.child.operation


@dataclass(frozen=True)
class PatchOperationForceFailed(PatchOperationResult):
    child: PatchOperationResult

    @property
    def is_successful(self) -> bool:
        return False

    @property
    def exception(self) -> Exception | None:
        return self.child.exception

    @property
    def nodes_affected(self) -> int:
        return self.child.nodes_affected

    @property
    def operation(self) -> PatchOperation:
        return self.child.operation


@dataclass(frozen=True)
class PatchOperationInverted(PatchOperationResult):
    child: PatchOperationResult

    @property
    def is_successful(self) -> bool:
        return not self.child.is_successful

    @property
    def exception(self) -> Exception | None:
        return self.child.exception

    @property
    def nodes_affected(self) -> int:
        return self.child.nodes_affected

    @property
    def operation(self) -> PatchOperation:
        return self.child.operation


@dataclass(frozen=True)
class PatchOperationDenied(PatchOperationResult):
    operation: PatchOperation

    @property
    def is_successful(self) -> bool:
        return True

    @property
    def exception(self) -> None:
        return

    @property
    def nodes_affected(self) -> int:
        return 0


@dataclass(frozen=True)
class PatchOperationSkipped(PatchOperationResult):
    operation: PatchOperation

    @property
    def is_successful(self) -> bool:
        return True

    @property
    def exception(self) -> None:
        return

    @property
    def nodes_affected(self) -> int:
        return 0
