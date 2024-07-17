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

    def __call__(
        self, xml: etree._ElementTree, context: "PatchContext"
    ) -> PatchOperationResult:
        """Apply the operation"""
        ...

    def to_xml(self, node: etree._Element):
        """Serialize the operation into an xml node"""
        ...


# pylint: disable-next=too-few-public-methods
class Patcher(Protocol):
    """Protocol for an operation deserializer

    Use it to select an operation from an xml node.

    Example:
        context = PatchContext(
                active_package_ids=[
                    "ludeon.rimworld", "ludeon.rimworld.royalty"
                    ],
                )

        def select_operation(node: etree._Element) -> PatchOperation:
            # create an operation
            ...


        patch_xml = etree.fromstring("<Operation Class="...">...</Operation>")
        result = select_operation(patch_xml)(xml, context)
    """

    def __call__(self, node: etree._Element) -> PatchOperation: ...


@dataclass(frozen=True)
class PatchContext:
    """Provides context for patch operations

    This is required for operations like PatchOperationFindMod, as well as
    filtering operations by MayRequire and MayRequireAnyOf attributes
    """

    active_package_ids: set[str]
    active_package_names: set[str]
