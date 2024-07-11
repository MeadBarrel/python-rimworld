from typing import Collection

from rimworld.mod import Mod
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



class BasePatcher(Patcher):
    def __init__(self, mods: Collection[Mod]|None=None) -> None:
        self._mods = mods or []
        self._active_package_ids = {mod.package_id for mod in self._mods}
        self._active_package_names = {mod.about.name for mod in self._mods if mod.about.name}
        super().__init__()

    def apply(self, xml: etree._Element, operation: PatchOperation) -> PatchOperationResult:
        if operation.meta.may_require and any (p not in self.active_package_ids for p in operation.meta.may_require):
            return PatchOperationDenied(operation)
        if operation.meta.may_require_any_of and all(p not in self.active_package_ids for p in operation.meta.may_require_any_of):
            return PatchOperationDenied(operation)
        match operation.meta.success:
            case Success.Always:
                op_result = operation.apply(xml, self)
                if op_result.is_successful():
                    return op_result
                return PatchOperationSuppressed(op_result)
            case Success.Normal:
                return operation.apply(xml, self)
            case Success.Invert:
                return PatchOperationInverted(
                        operation.apply(xml, self)
                        )
            case Success.Never:
                return PatchOperationDenied(operation)

    def select_operation(self, node: etree._Element) -> PatchOperation:
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
                raise MalformedPatchError(f'Unknown operation class: {class_} ({node.tag})')

    @property
    def active_package_ids(self) -> set[str]:
        return self._active_package_ids

    @property
    def active_package_names(self) -> set[str]:
        return self._active_package_names


