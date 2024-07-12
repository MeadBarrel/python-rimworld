from dataclasses import dataclass
from lxml import etree
from copy import deepcopy
from typing import Self, cast
from abc import abstractmethod
from rimworld.base import *


__all__ = [
        'SafeElement',
        'get_xpath',
        'get_value',
        'get_text',
        'get_element',
        'xpath_elements',
        'get_order_append',
        'PatchOperationMetaResult',
        'PatchOperationSuppressed',
        'PatchOperationInverted',
        'PatchOperationDenied',
        'PatchOperationFailure',
        'PatchOperationMeta',
        'PatchOperation',
        ]


@dataclass(frozen=True)
class SafeElement:
    element: etree._Element

    def copy(self) -> etree._Element:
        return deepcopy(self.element)


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
class PatchOperation(PatchOperationBase):
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


def xpath_elements(world: World, xpath: str) -> list[etree._Element]:
    found = world.xpath(xpath)

    if isinstance(found , etree._Element):
        found = [found]
    if not (isinstance(found, list) and all(isinstance(x, etree._Element) for x in found)):
        raise MalformedPatchError('xpath returned unexpected results')
    return cast(list[etree._Element], found)


def get_order_append(xml: etree._Element, default: bool) -> bool:
    order_elt = xml.find('order')
    if order_elt is not None:
        if not order_elt.text or order_elt.text not in ('Prepend', 'Append'):
            raise MalformedPatchError('order should be either Append or Prepend')
        return order_elt.text == 'Append'
    return default

