from copy import deepcopy
from dataclasses import dataclass, field
from typing import Self, Sequence, Type, NamedTuple, cast
from .gameversion import GameVersion
from lxml import etree
from .mod import Mod
from functools import cached_property
from abc import ABC, abstractmethod
from enum import Enum, auto
from .settings import Settings
from pathlib import Path
from .xml import load_xml


__all__ = [
        'Modlist',
        'MalformedPatchError',
        'PatchError',
        'Success',
        'World',
        'UnknownPatchOperationError',
        'PatchOperationResult',
        'PatchOperationBase',
        'load_mod_infos',
        'is_mod_folder',
        'unused',
        ]


class Modlist(NamedTuple):
    active_package_ids: list[str]
    known_expansions: list[str]


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

    @classmethod
    def from_settings(cls, settings: Settings):
        raise NotImplementedError()

    def copy(self) -> Self:
        return deepcopy(self)

    def load(self, apply_patches: bool=True):
        """ Recreate the data and load all mods """
        raise NotImplementedError()

    def load_mods(self, mods: list[Mod], apply_patches: bool=True):
        """ Add new mods and load them """
        raise NotImplementedError()

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

    def xpath(self, xpath: str):
        if not xpath.startswith('/'):
            xpath = '/' + xpath
        return self.xml.xpath(xpath)

    @cached_property
    def active_package_ids(self) -> set[str]:
        return {mod.package_id for mod in self.mods}

    @cached_property
    def active_package_names(self) -> set[str]:
        return {mod.about.name for mod in self.mods if mod.about.name}

    def _load_mods(self, mods: Sequence[Mod]):
        pass


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


def load_mod_infos(paths: Path|Sequence[Path]) -> list[Mod]:
    if isinstance(paths, Path):
        if not paths.is_dir():
            return []
        if is_mod_folder(paths):
            return [Mod.load(paths)]
        return load_mod_infos(list(paths.iterdir()))
    
    result = []
    for p in paths:
        result.extend(load_mod_infos(p))

    return result


def is_mod_folder(path: Path) -> bool:
    p = path.joinpath('About', 'About.xml')
    return p.exists() and p.is_file()


def read_modlist(filepath: Path) -> Modlist:
    """
    Read and parse the modlist XML file.


    Args:
        filepath (Path): The path to the modlist XML file.

    Returns:
        _Modlist: A _Modlist instance containing active mod package IDs and known expansions.

    Raises:
        AssertionError: If the parsed XML does not contain expected elements.
    """    
    xml = load_xml(filepath)

    mods = xml.xpath('/ModsConfigData/activeMods/*/text()')
    assert isinstance(mods, list)
    assert all(isinstance(x, str) for x in mods)

    known_expansions = xml.xpath('/ModsConfigData/knownExpansions/*/text()')
    assert isinstance(known_expansions, list)
    assert all(isinstance(x, str) for x in known_expansions)

    return Modlist(cast(list[str], mods), cast(list[str], known_expansions))



def unused(_):
    pass
