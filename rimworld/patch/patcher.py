from lxml import etree
from rimworld.worldsettings import WorldSettings
from .proto import *
from typing import Self
from enum import Enum, auto
from ._base import MalformedPatchError
from .result import *

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


class Success(Enum):
    Always = auto()
    Normal = auto()
    Invert = auto()
    Never  = auto()

    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        elt = node.find('success')
        if elt is None:
            return Success.Normal
        match elt.text:
            case 'Always':
                return Success.Always
            case 'Never':
                return Success.Never
            case 'Normal':
                return Success.Normal
            case 'Invert':
                return Success.Invert
            case _:
                raise MalformedPatchError(f'Incorrect `success` tag value: {elt.text}')


@dataclass(frozen=True)
class PatchOperationWrapper(PatchOperation):
    operation: PatchOperation
    may_require: list[str]|None = None
    may_require_any_of: list[str]|None = None
    success: Success = Success.Normal

    def apply(self, context: PatchContext) -> PatchOperationResult:
        if self.may_require:
            if not all(pid in context.settings.active_package_ids for pid in self.may_require):
                return PatchOperationDenied(self.operation)
        if self.may_require_any_of:
            if not any(pid in context.settings.active_package_ids for pid in self.may_require_any_of):
                return PatchOperationDenied(self.operation)
        op_result = context.apply_operation(self.operation)
        match self.success:
            case Success.Normal:
                return op_result
            case Success.Always:
                return PatchOperationSuppressed(op_result)
            case Success.Never:
                return PatchOperationForceFailed(op_result)
            case Success.Invert:
                return PatchOperationInverted(op_result)


class PatchOperationUnknown:
    def apply(self, context: PatchContext) -> 'PatchOperationResult':
        return PatchOperationSkipped(self)


class WorldPatcher(Patcher):
    def patch(self, xml: etree._ElementTree, patch: etree._ElementTree, settings: WorldSettings) -> list[PatchOperationResult]:
        operations = self.collect_operations(patch.getroot(), 'Operation')
        return [self.apply_operation(xml, operation, settings) for operation in operations]

    def apply_operation(self, xml: etree._ElementTree, operation: PatchOperation, settings: WorldSettings) -> PatchOperationResult:
        return operation.apply(
                PatchContext(
                    xml,
                    settings,
                    self,
                    )
                )

    def collect_operations(self, node: etree._Element, tag: str) -> list[PatchOperation]:
        return [self.select_operation(sn) for sn in node if sn.tag == tag]

    def select_operation(self, node: etree._Element) -> PatchOperation:
        base_op = self._select_operation_concrete(node)

        if isinstance(base_op, PatchOperationUnknown):
            return base_op

        may_require = None
        may_require_any_of = None

        if mr:=node.get('MayRequire'):
            may_require = [x.strip() for x in mr.split(',')]
        if mr:=node.get('MayRequireAnyOf'):
            may_require_any_of = [x.strip() for x in mr.split(',')]
        success = Success.from_xml(node)

        if may_require or may_require_any_of or success != Success.Normal:
            return PatchOperationWrapper(
                    base_op,
                    may_require,
                    may_require_any_of,
                    success
                    )

        return base_op

    def _select_operation_concrete(self, node: etree._Element) -> PatchOperation:
        match node.get('Class'):
            case 'PatchOperationAdd':
                return PatchOperationAdd.from_xml(node)
            case 'PatchOperationAddModExtension':
                return PatchOperationAddModExtension.from_xml(node)
            case 'PatchOperationAttributeAdd':
                return PatchOperationAttributeAdd.from_xml(node)
            case 'PatchOperationAttributeRemove':
                return PatchOperationAttributeRemove.from_xml(node)
            case 'PatchOperationAttributeSet':
                return PatchOperationAttributeSet.from_xml(node)
            case 'PatchOperationConditional':
                return PatchOperationConditional.from_xml(self, node)
            case 'PatchOperationFindMod':
                return PatchOperationFindMod.from_xml(self, node)
            case 'PatchOperationInsert':
                return PatchOperationInsert.from_xml(node)
            case 'PatchOperationTest':
                return PatchOperationTest.from_xml(node)
            case 'PatchOperationRemove':
                return PatchOperationRemove.from_xml(node)
            case 'PatchOperationReplace':
                return PatchOperationReplace.from_xml(node)
            case 'PatchOperationSequence':
                return PatchOperationSequence.from_xml(self, node)
            case 'PatchOperationSetName':
                return PatchOperationSetName.from_xml(node)
            case _:
                return PatchOperationUnknown()
