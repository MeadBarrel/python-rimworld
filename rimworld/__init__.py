from .gameversion import *
from dataclasses import field, dataclass
from typing import Type
from .base import World, PatchOperation
from .patch.add import PatchOperationAdd
from .patch.insert import PatchOperationInsert
from .patch.remove import PatchOperationRemove
from .patch.replace import PatchOperationReplace
from .patch.attributeadd import PatchOperationAttributeAdd
from .patch.attributeset import PatchOperationAttributeSet
from .patch.attributeremove import PatchOperationAttributeRemove
from .patch.setname import PatchOperationSetName
from .patch.addmodextension import PatchOperationAddModExtension
from .patch.sequence import PatchOperationSequence
from .patch.findmod import PatchOperationFindMod
from .patch.conditional import PatchOperationConditional
from .patch.op_test import PatchOperationTest


DEFAULT_PATCH_OPERATIONS = [
            PatchOperationAdd,
            PatchOperationInsert,
            PatchOperationRemove,
            PatchOperationReplace,
            PatchOperationAttributeAdd,
            PatchOperationAttributeSet,
            PatchOperationAttributeRemove,
            PatchOperationSetName,
            PatchOperationAddModExtension,
            PatchOperationSequence,
            PatchOperationFindMod,
            PatchOperationConditional,
            PatchOperationTest,
        ]


@dataclass
class Rimworld(World):
    patch_operations: list[Type[PatchOperation]] = field(default_factory=lambda: DEFAULT_PATCH_OPERATIONS)
