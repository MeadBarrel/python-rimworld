"""
Provides xml patching functionality

First, you need a patch context. A patch context contains some information
about rimworld's configuration that may be needed by the patching process,
like what mods are enabled.

>>> context = PatchContext(
...     active_package_ids=["ludeon.rimworld", "unlimitedhugs.allowtool"],
...     active_package_names=["Allow Tool"]
...     )

Now, define an empty Defs xml and an xml for our patch operation

>>> defs = etree.ElementTree(etree.Element('Defs'))
>>> operation_node = etree.fromstring('''
... <Operation Class="PatchOperationAdd">
...     <xpath>/Defs</xpath>
...     <value><thingDef><defName>dummy_def</defName></thingDef></value>
... </Operation>
... ''')

Now, you need a function to deserialize that patch operation. It should 
conform to `Patch` protocol. This module defines one such function, which
should be enough for most of your needs:

>>> operation = get_operation(operation_node)

We can now apply that operation to the Defs xml defined previously

>>> operation(defs, context)
PatchOperationBasicCounterResult(operation=..., nodes_affected=1)

"""

from copy import deepcopy
from dataclasses import dataclass
from enum import Enum, auto
from typing import Self

from lxml import etree

from rimworld.error import MalformedPatchError

from .operations.add import PatchOperationAdd
from .operations.addmodextension import PatchOperationAddModExtension
from .operations.attributeadd import PatchOperationAttributeAdd
from .operations.attributeremove import PatchOperationAttributeRemove
from .operations.attributeset import PatchOperationAttributeSet
from .operations.conditional import PatchOperationConditional
from .operations.findmod import PatchOperationFindMod
from .operations.insert import PatchOperationInsert
from .operations.op_test import PatchOperationTest
from .operations.remove import PatchOperationRemove
from .operations.replace import PatchOperationReplace
from .operations.sequence import PatchOperationSequence
from .operations.setname import PatchOperationSetName
from .proto import PatchContext, PatchOperation, PatchOperationResult
from .result import (PatchOperationDenied, PatchOperationForceFailed,
                     PatchOperationInverted, PatchOperationSkipped,
                     PatchOperationSuppressed)
from .xmlextensions.addorreplace import PatchOperationAddOrReplace
from .xmlextensions.safeadd import PatchOperationSafeAdd

__all__ = [
    "PatchOperationAdd",
    "PatchOperationAddModExtension",
    "PatchOperationAttributeRemove",
    "PatchOperationAttributeSet",
    "PatchOperationConditional",
    "PatchOperationFindMod",
    "PatchOperationInsert",
    "PatchOperationTest",
    "PatchOperationRemove",
    "PatchOperationReplace",
    "PatchOperationSequence",
    "PatchOperationSetName",
    "PatchOperationAddOrReplace",
    "PatchOperationSafeAdd",
    "PatchContext",
    "PatchOperation",
    "PatchOperationResult",
    "PatchOperationDenied",
    "PatchOperationForceFailed",
    "PatchOperationInverted",
    "PatchOperationSkipped",
    "PatchOperationSuppressed",
    "PatchOperationWrapper",
    "get_operation",
    "Success",
]


class Success(Enum):
    """Success tag of an operation"""

    ALWAYS = auto()
    NORMAL = auto()
    INVERT = auto()
    NEVER = auto()

    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        """Deserialize from xml"""
        elt = node.find("success")
        if elt is None:
            return Success.NORMAL
        match elt.text:
            case "Always":
                return Success.ALWAYS
            case "Never":
                return Success.NEVER
            case "Normal":

                return Success.NORMAL
            case "Invert":
                return Success.INVERT
            case _:
                raise MalformedPatchError(f"Incorrect `success` tag value: {elt.text}")


@dataclass(frozen=True)
class PatchOperationWrapper(PatchOperation):
    """Wrapper around common operations

    Provides common functionality like handling MayRequire attributes,
    as well as <success> tags
    """

    operation: PatchOperation
    may_require: list[str] | None = None
    may_require_any_of: list[str] | None = None
    success: Success = Success.NORMAL

    def __call__(
        self, xml: etree._ElementTree, context: PatchContext
    ) -> PatchOperationResult:
        if self.may_require:
            if not all(pid in context.active_package_ids for pid in self.may_require):
                return PatchOperationDenied(self.operation)
        if self.may_require_any_of:
            if not any(
                pid in context.active_package_ids for pid in self.may_require_any_of
            ):
                return PatchOperationDenied(self.operation)
        op_result = self.operation(xml, context)
        match self.success:
            case Success.NORMAL:
                return op_result
            case Success.ALWAYS:
                return PatchOperationSuppressed(op_result)
            case Success.NEVER:
                return PatchOperationForceFailed(op_result)
            case Success.INVERT:
                return PatchOperationInverted(op_result)

    def to_xml(self, node: etree._Element):
        self.operation.to_xml(node)
        if self.may_require:
            node.set("MayRequire", ",".join(self.may_require))
        if self.may_require_any_of:
            node.set("MayRequireAnyOf", ",".join(self.may_require_any_of))
        if self.success == Success.NORMAL:
            return
        n = etree.Element("success")
        match self.success:
            case Success.ALWAYS:
                n.text = "Always"
            case Success.NEVER:
                n.text = "Never"
            case Success.INVERT:
                n.text = "Invert"


@dataclass
class PatchOperationUnknown(PatchOperation):
    """Represents a patch operation not supported by the patcher"""

    node: etree._Element

    def __call__(self, *_) -> "PatchOperationResult":
        return PatchOperationSkipped(self)

    def to_xml(self, node: etree._Element):
        n = deepcopy(self.node)
        for k, v in n.attrib.items():
            node.set(k, v)
        for c in n:
            node.append(c)


def get_operation(node: etree._Element) -> PatchOperation:
    """Basic Patcher"""
    base_op = _select_operation_concrete(node)

    if isinstance(base_op, PatchOperationUnknown):
        return base_op

    may_require = None
    may_require_any_of = None

    if mr := node.get("MayRequire"):
        may_require = [x.strip() for x in mr.split(",")]
    if mr := node.get("MayRequireAnyOf"):
        may_require_any_of = [x.strip() for x in mr.split(",")]
    success = Success.from_xml(node)

    if may_require or may_require_any_of or success != Success.NORMAL:
        return PatchOperationWrapper(base_op, may_require, may_require_any_of, success)

    return base_op


# pylint: disable-next=too-many-return-statements
def _select_operation_concrete(node: etree._Element) -> PatchOperation:
    match node.get("Class"):
        case "PatchOperationAdd":
            return PatchOperationAdd.from_xml(node)
        case "PatchOperationAddModExtension":
            return PatchOperationAddModExtension.from_xml(node)
        case "PatchOperationAttributeAdd":
            return PatchOperationAttributeAdd.from_xml(node)
        case "PatchOperationAttributeRemove":
            return PatchOperationAttributeRemove.from_xml(node)
        case "PatchOperationAttributeSet":
            return PatchOperationAttributeSet.from_xml(node)
        case "PatchOperationConditional":
            return PatchOperationConditional.from_xml(get_operation, node)
        case "PatchOperationFindMod":
            return PatchOperationFindMod.from_xml(get_operation, node)
        case "PatchOperationInsert":
            return PatchOperationInsert.from_xml(node)
        case "PatchOperationTest":
            return PatchOperationTest.from_xml(node)
        case "PatchOperationRemove":
            return PatchOperationRemove.from_xml(node)
        case "PatchOperationReplace":
            return PatchOperationReplace.from_xml(node)
        case "PatchOperationSequence":
            return PatchOperationSequence.from_xml(get_operation, node)
        case "PatchOperationSetName":
            return PatchOperationSetName.from_xml(node)

        # XmlExtensions
        case "XmlExtensions.PatchOperationSafeAdd":
            return PatchOperationSafeAdd.from_xml(node)
        case "XmlExtensions.PatchOperationAddOrReplace":
            return PatchOperationAddOrReplace.from_xml(node)

        case _:
            return PatchOperationUnknown(node)
