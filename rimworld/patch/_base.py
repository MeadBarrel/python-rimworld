from dataclasses import dataclass
from enum import Enum, auto
from lxml import etree
from copy import deepcopy
from abc import ABC, abstractmethod, abstractproperty
from typing import Self, cast

__all__ = [
        'MalformedPatchError',
        'PatchError',
        'Success',
        'SafeElement',
        'PatchOperationResult',
        'Patcher',
        'PatchOperationMeta',
        'PatchOperation',
        'get_xpath',
        'get_value',
        'get_text',
        'get_element',
        'xpath_elements',
        'get_order_append',
        'unused'
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


@dataclass(frozen=True)
class SafeElement:
    element: etree._Element

    def copy(self) -> etree._Element:
        return deepcopy(self.element)


class PatchOperationResult(ABC):
    @abstractmethod
    def is_successful(self) -> bool:
        ...

    @abstractmethod
    def exception(self) -> Exception|None:
        ...

    @abstractmethod
    def count_nodes_affected(self) -> int:
        ...


class Patcher(ABC):
    def patch(self, xml: etree._ElementTree, patch: etree._Element) -> list[PatchOperationResult]:
        operations = self.collect_patches(patch)
        return [self.apply(xml, operation) for operation in operations]

    def apply(self, xml: etree._ElementTree, operation: 'PatchOperation') -> PatchOperationResult:
        return operation.apply(xml, self)

    def collect_patches(self, patch: etree._Element, tag: str='Operation') -> list['PatchOperation']:
        return [
                self.select_operation(patch_node)
                for patch_node in patch
                if patch_node.tag == tag
                ]

    @abstractmethod
    def select_operation(self, node: etree._Element) -> 'PatchOperation':
        ...

    @abstractproperty
    def active_package_ids(self) -> set[str]:
        ...

    @abstractproperty
    def active_package_names(self) -> set[str]:
        ...

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
    
    @abstractmethod
    def apply(self, xml: etree._ElementTree, patcher: Patcher) -> PatchOperationResult:
        ...


def get_xpath(xml: etree._Element) -> str:
    elt = xml.find('xpath')
    if elt is None:
        raise MalformedPatchError('Element not found: xpath')
    if not elt.text:
        raise MalformedPatchError('xpath element has no text')
    xpath = elt.text
    if not xpath.startswith('/'):
        xpath = '/' + xpath
    return xpath
    
    
def get_value(xml: etree._Element) -> list[SafeElement]:
    elt = xml.find('value')
    if elt is None:
        raise MalformedPatchError('Element not found: value')
    return [SafeElement(e) for e in elt]


def get_text(xml: etree._Element, tag: str) -> str:
    elt = xml.find(tag)
    if elt is None:
        raise MalformedPatchError(f'Element not found: {tag}')
    return elt.text or ''

def get_element(xml: etree._Element, tag: str) -> etree._Element:
    elt = xml.find(tag)
    if elt is None:
        raise MalformedPatchError(f'Element not found: {tag}')
    return elt


def xpath_elements(xml: etree._ElementTree, xpath: str) -> list[etree._Element]:
    found = xml.xpath(xpath)

    if isinstance(found , etree._Element):
        found = [found]
    if not (isinstance(found, list) and all(isinstance(x, etree._Element) for x in found)):
        raise PatchError('xpath returned unexpected results')
    return cast(list[etree._Element], found)


def get_order_append(xml: etree._Element, default: bool) -> bool:
    order_elt = xml.find('order')
    if order_elt is not None:
        if not order_elt.text or order_elt.text not in ('Prepend', 'Append'):
            raise MalformedPatchError('order should be either Append or Prepend')
        return order_elt.text == 'Append'
    return default


def unused(_):
    pass
