""" Base definitions for patching """

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from lxml import etree


class PatchOperationResult(Protocol):  # pylint: disable=R0903
    """Result of a patch operation"""

    operation: "PatchOperation"
    nodes_affected: int
    exception: Exception | None
    is_successful: bool


@runtime_checkable
class PatchOperation(Protocol):
    """Base class for all patch operations"""

    def apply(
        self, patcher: "Patcher", context: "PatchContext"
    ) -> PatchOperationResult:
        """Apply the operation"""
        ...

    def to_xml(self, node: etree._Element):
        """Serialize the operation into an xml node"""
        ...


class Patcher(Protocol):
    """Patching controller"""

    def patch(
        self,
        patch: etree._ElementTree,
        context: "PatchContext",
    ) -> list[PatchOperationResult]:
        """Apply operations defined in `patch` on context.xml"""
        ...

    def collect_operations(
        self,
        node: etree._Element,
        tag: str,
    ) -> list[PatchOperation]:
        """Collect operations from a node"""
        ...

    def select_operation(
        self,
        node: etree._Element,
    ) -> PatchOperation:
        """Select an operation defined in a node"""
        ...

    def apply_operation(
        self,
        operation: PatchOperation,
        context: "PatchContext",
    ) -> PatchOperationResult:
        """Appy an operation"""
        ...


@dataclass(frozen=True)
class PatchContext:
    """Provides context for patch operations"""

    xml: etree._ElementTree
    active_package_ids: set[str]
    active_package_names: set[str]
