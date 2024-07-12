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
        'PatchOperationBase',
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
    patch_operations: list[Type['PatchOperationBase']] = field(default_factory=list)
    skip_unknown_operations: bool = False


    def merge(self, xml: etree._ElementTree):
        for node in xml.getroot():
            self.xml.getroot().append(node)

    def patch(self, xml: etree._ElementTree) -> 'list[PatchOperationResult]':
        operations = self.collect_patch_operations(xml.getroot())
        return [operation.apply(self) for operation in operations]

    def collect_patch_operations(self, root: etree._Element, tag: str='Operation') -> list['PatchOperationBase']:
        result = []
        for node in root:
            if node.tag != tag:
                continue
            operation = self.select_patch_operation(node)
            if operation is None:
                continue
            result.append(operation)
        return result

    def select_patch_operation(self, node: etree._Element) -> 'PatchOperationBase|None':
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
class PatchOperationBase(ABC):
    @abstractmethod
    def apply(self, world: World) -> PatchOperationResult:
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
