from typing import Collection

from rimworld.mod import Mod
from rimworld.rimworld import Rimworld
from ._base import *
from lxml import etree
from ._result import *

from .add import PatchOperationAdd
from .insert import PatchOperationInsert
from .remove import PatchOperationRemove
from .replace import PatchOperationReplace
from .attributeadd import PatchOperationAttributeAdd
from .attributeset import PatchOperationAttributeSet
from .attributeremove import PatchOperationAttributeRemove
from .addmodextension import PatchOperationAddModExtension
from .setname import PatchOperationSetName
from .sequence import PatchOperationSequence
from .findmod import PatchOperationFindMod
from .conditional import PatchOperationConditional
from .op_test import PatchOperationTest


class UnknownPatchOperation(MalformedPatchError):
    pass


class BasePatcher(Patcher):
    @property
    def skip_unknown_operations(self) -> bool:
        return self._skip_unknown_operations

    def apply(self, rimworld: Rimworld, xml: etree._ElementTree, operation: PatchOperation) -> PatchOperationResult:
        if operation.meta.may_require and any (p not in rimworld.active_package_ids for p in operation.meta.may_require):
            return PatchOperationDenied(operation)
        if operation.meta.may_require_any_of and all(p not in rimworld.active_package_ids for p in operation.meta.may_require_any_of):
            return PatchOperationDenied(operation)
        match operation.meta.success:
            case Success.Always:
                op_result = operation.apply(xml, self, rimworld)
                if op_result.is_successful():
                    return op_result
                return PatchOperationSuppressed(op_result)
            case Success.Normal:
                return operation.apply(xml, self, rimworld)
            case Success.Invert:
                return PatchOperationInverted(
                        operation.apply(xml, self, rimworld)
                        )
            case Success.Never:
                return PatchOperationDenied(operation)

    def select_operation(self, node: etree._Element) -> 'PatchOperation|None':
        match class_ := node.get('Class'):
            case 'PatchOperationAdd':
                return PatchOperationAdd.from_xml(node)
            case 'PatchOperationInsert':
                return PatchOperationInsert.from_xml(node)
            case 'PatchOperationRemove':
                return PatchOperationRemove.from_xml(node)
            case 'PatchOperationReplace':
                return PatchOperationReplace.from_xml(node)
            case 'PatchOperationAttributeAdd':
                return PatchOperationAttributeAdd.from_xml(node)
            case 'PatchOperationAttributeSet':
                return PatchOperationAttributeSet.from_xml(node)
            case 'PatchOperationAttributeRemove':
                return PatchOperationAttributeRemove.from_xml(node)
            case 'PatchOperationAddModExtension':
                return PatchOperationAddModExtension.from_xml(node)
            case 'PatchOperationSetName':
                return PatchOperationSetName.from_xml(node)
            case 'PatchOperationSequence':
                return PatchOperationSequence.from_xml(node, self)
            case 'PatchOperationFindMod':
                return PatchOperationFindMod.from_xml(node, self)
            case 'PatchOperationConditional':
                return PatchOperationConditional.from_xml(node, self)
            case 'PatchOperationTest':
                return PatchOperationTest.from_xml(node)
            case _:
                if self.skip_unknown_operations:
                    return None
                raise UnknownPatchOperation(class_)


