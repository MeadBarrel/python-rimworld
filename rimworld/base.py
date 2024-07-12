from dataclasses import dataclass, field
from typing import Self, Type
from .gameversion import GameVersion
from lxml import etree
from .mod import Mod
from functools import cached_property
from abc import ABC, abstractmethod
from enum import Enum, auto


__all__ = [
        'MalformedPatchError',
        'PatchError',
        'Success',
        'World',
        'UnknownPatchOperationError',
        'PatchOperationResult',
        'PatchOperationMeta',
        'PatchOperation',
        'unused',
        ]


class MalformedPatchError(Exception):
    pass


class PatchError(Exception):
    pass


class Success(Enum):
    Always = auto()
    Normal = auto()
    Invert = auto()
    Never  = auto()


@dataclass
class World:
    mods: list[Mod] = field(default_factory=list)
    version: GameVersion|None = None
    xml: etree._ElementTree = field(default_factory=lambda: etree.ElementTree(etree.Element('Defs')))
    patch_operations: list[Type['PatchOperation']] = field(default_factory=list)
    skip_unknown_operations: bool = False


    def merge(self, xml: etree._ElementTree):
        for node in xml.getroot():
            self.xml.getroot().append(node)

    def patch(self, xml: etree._ElementTree) -> 'list[PatchOperationResult]':
        operations = self.collect_patch_operations(xml.getroot())
        return [operation.apply(self) for operation in operations]

    def collect_patch_operations(self, root: etree._Element, tag: str='Operation') -> list['PatchOperation']:
        result = []
        for node in root:
            if node.tag != tag:
                continue
            operation = self.select_patch_operation(node)
            if operation is None:
                continue
            result.append(operation)
        return result

    def select_patch_operation(self, node: etree._Element) -> 'PatchOperation|None':
        class_ = node.get('Class')
        if not class_:
            return 
        
        for operation_cls in self.patch_operations:
            if operation_cls.class_() == class_:
                return operation_cls.from_xml(self, node)

        if self.skip_unknown_operations:
            return

        raise UnknownPatchOperationError()


    @cached_property
    def active_package_ids(self) -> set[str]:
        return {mod.package_id for mod in self.mods}

    @cached_property
    def active_package_names(self) -> set[str]:
        return {mod.about.name for mod in self.mods if mod.about.name}


class UnknownPatchOperationError(Exception):
    pass


class PatchOperationResult(ABC):
    @abstractmethod
    def is_successful(self) -> bool:
        ...

    @abstractmethod
    def exception(self) -> Exception|None:
        ...

    @abstractmethod
    def nodes_affected(self) -> int:
        pass


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

    def nodes_affected(self) -> int:
        return self.child.nodes_affected()




@dataclass(frozen=True)
class PatchOperationInverted(PatchOperationMetaResult):
    child: PatchOperationResult

    def is_successful(self) -> bool:
        return not self.child.is_successful()

    def exception(self) -> Exception|None:
        return self.child.exception()

    def nodes_affected(self) -> int:
        return self.child.nodes_affected()



@dataclass(frozen=True)
class PatchOperationDenied(PatchOperationMetaResult):
    operation: 'PatchOperation'

    def is_successful(self) -> bool:
        return False

    def exception(self) -> Exception|None:
        return None

    def nodes_affected(self) -> int:
        return 0


@dataclass(frozen=True)
class PatchOperationFailure(PatchOperationMetaResult):
    operation: 'PatchOperation'
    error: Exception

    def is_successful(self) -> bool:
        return False

    def exception(self) -> Exception:
        return self.error

    def nodes_affected(self) -> int:
        return 0


@dataclass(frozen=True)
class PatchOperationMeta:
    may_require: list[str]|None = None
    may_require_any_of: list[str]|None = None
    success: Success = Success.Normal

    @classmethod
    def from_xml(cls, node: etree._Element) -> Self:
        may_require = None
        may_require_any_of = None

        if may_require_record := node.get('MayRequire'):
            may_require = [x.strip().lower() for x in may_require_record.split(',')]
        if may_require_any_of_record := node.get('MayRequireAnyOf'):
            may_require_any_of = [x.strip().lower() for x in may_require_any_of_record.split(',')]

        match node.find('success'):
            case etree._Element(text='Always'):
                success = Success.Always
            case etree._Element(text='Normal'):
                success = Success.Normal
            case etree._Element(text='Invert'):
                success = Success.Invert
            case etree._Element(text='Never'):
                success = Success.Never
            case None:
                success = Success.Normal
            case _:
                raise MalformedPatchError('Incorrect success element')


        return cls(may_require, may_require_any_of, success)


@dataclass(frozen=True)
class PatchOperation(ABC):
    meta: PatchOperationMeta

    def apply(self, world: World) -> PatchOperationResult:
        if self.meta.may_require and any (p not in world.active_package_ids for p in self.meta.may_require):
            return PatchOperationDenied(self)
        if self.meta.may_require_any_of and all(p not in world.active_package_ids for p in self.meta.may_require_any_of):
            return PatchOperationDenied(self)
        match self.meta.success:
            case Success.Always:
                op_result = self._apply(world)
                if op_result.is_successful():
                    return op_result
                return PatchOperationSuppressed(op_result)
            case Success.Normal:
                return self._apply(world)
            case Success.Invert:
                return PatchOperationInverted(
                        self._apply(world)
                        )
            case Success.Never:
                return PatchOperationDenied(self)

    @abstractmethod
    def _apply(self, world: World) -> PatchOperationResult:
        ...

    @classmethod
    def from_xml(cls, world: World, node: etree._Element) -> Self:
        unused(world)
        unused(node)
        raise NotImplementedError()

    @classmethod
    def class_(cls) -> str:
        return cls.__name__

        
def unused(_):
    pass
