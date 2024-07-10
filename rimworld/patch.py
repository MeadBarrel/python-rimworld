from dataclasses import dataclass, field
from typing import Collection, Sequence, cast, Self
from lxml import etree

from rimworld.mod import Mod


class MalformedPatchError(Exception):
    pass


class PatchError(Exception):
    pass




@dataclass(frozen=True)
class PatchOperation:
    def __call__(self, xml: etree._Element, mods: Collection[Mod]):
        unused(xml)
        unused(mods)
        raise NotImplementedError()


@dataclass(frozen=True)
class PatchOperationMeta(PatchOperation):
    operation: PatchOperation
    may_require: list[str]|None = None
    may_require_any_of: list[str]|None = None

    def __call__(self, xml: etree._Element, mods: Collection[Mod]):
        if self.should_call(mods):
            self.operation(xml, mods)

    def should_call(self, mods: Collection[Mod]):
        package_ids = {m.package_id for m in mods}
        if self.may_require and any(p not in package_ids for p in self.may_require):
            return False
        if self.may_require_any_of and all(p not in package_ids for p in self.may_require_any_of):
            return False
        return True


    @classmethod
    def from_xml(cls, operation_elt: etree._Element) -> Self:
        may_require = None
        may_require_any_of = None

        if may_require_record := operation_elt.get('MayRequire'):
            may_require = [x.strip().lower() for x in may_require_record.split(',')]
        if may_require_any_of_record := operation_elt.get('MayRequireAnyOf'):
            may_require_any_of = [x.strip().lower() for x in may_require_any_of_record.split(',')]
        operation = _select_operation(operation_elt)
        return cls(operation, may_require, may_require_any_of)


@dataclass(frozen=True)
class PatchOperationAdd(PatchOperation):
    xpath: str
    value: list[etree._Element]
    append: bool

    def __call__(self, xml: etree._Element, _):
        found = xpath_elements(xml, self.xpath)

        if self.append:
            for elt in found:
                elt.extend(self.value)
        else:
            for elt in found:
                for v in self.value:
                    elt.insert(0, v)

        pass

    @classmethod
    def from_xml(cls, operation_elt: etree._Element) -> Self:
        xpath = _get_xpath(operation_elt)
        value = _get_value(operation_elt)
        append = get_order_append(operation_elt, True)

        return cls(xpath, value, append)


@dataclass(frozen=True)
class PatchOperationInsert(PatchOperation):
    xpath: str
    value: list[etree._Element]
    append: bool

    def __call__(self, xml: etree._Element, _):
        found = xpath_elements(xml, self.xpath)
        if self.append:
            for f in found:
                for v in reversed(self.value):
                    f.addnext(v)
        else:
            for f in found:
                for v in self.value:
                    f.addprevious(v)

    @classmethod
    def from_xml(cls, operation_elt: etree._Element) -> Self:
        xpath = _get_xpath(operation_elt)
        value = _get_value(operation_elt)
        append = get_order_append(operation_elt, False)
        return cls(xpath, value, append)


@dataclass(frozen=True)
class PatchOperationRemove(PatchOperation):
    xpath: str

    def __call__(self, xml: etree._Element, _):
        found = xpath_elements(xml, self.xpath)
        for elt in found:
            parent = elt.getparent()
            if parent is None:
                raise PatchError(f'Parent not found for {self.xpath}')
            parent.remove(elt)

    @classmethod
    def from_xml(cls, operation_elt: etree._Element) -> Self:
        xpath = _get_xpath(operation_elt)
        return cls(xpath)


@dataclass(frozen=True)
class PatchOperationReplace(PatchOperation):
    xpath: str
    value: list[etree._Element]

    def __call__(self, xml: etree._Element, _):
        found = xpath_elements(xml, self.xpath)

        for f in found:
            parent = f.getparent()
            if parent is None:
                raise PatchError(f'Parent not found for {self.xpath}')
            v1, *v_ = self.value
            parent.replace(f, v1)

            for v in reversed(v_):
                v1.addnext(v)

    @classmethod
    def from_xml(cls, operation_elt: etree._Element) -> Self:
        xpath = _get_xpath(operation_elt)
        value = _get_value(operation_elt)
        return cls(xpath, value)


@dataclass(frozen=True)
class PatchOperationAttributeAdd(PatchOperation):
    xpath: str
    attribute: str
    value: str

    def __call__(self, xml: etree._Element, _):
        found = xpath_elements(xml, self.xpath)

        for elt in found:
            if elt.get(self.attribute) is not None:
                continue
            elt.set(self.attribute, self.value)

    @classmethod
    def from_xml(cls, operation_elt: etree._Element) -> Self:
        xpath = _get_xpath(operation_elt)
        attribute = _get_text(operation_elt, 'attribute')
        value = _get_text(operation_elt, 'value')
        return cls(xpath, attribute, value)


@dataclass(frozen=True)
class PatchOperationAttributeSet(PatchOperation):
    xpath: str
    attribute: str
    value: str

    def __call__(self, xml: etree._Element, _):
        found = xpath_elements(xml, self.xpath)

        for elt in found:
            elt.set(self.attribute, self.value)

    @classmethod
    def from_xml(cls, operation_elt: etree._Element) -> Self:
        xpath = _get_xpath(operation_elt)
        attribute = _get_text(operation_elt, 'attribute')
        value = _get_text(operation_elt, 'value')
        return cls(xpath, attribute, value)


@dataclass(frozen=True)
class PatchOperationAttributeRemove(PatchOperation):
    xpath: str
    attribute: str

    def __call__(self, xml: etree._Element, _):
        found = xpath_elements(xml, self.xpath)

        for elt in found:
            elt.attrib.pop(self.attribute)

    @classmethod
    def from_xml(cls, operation_elt: etree._Element) -> Self:
        xpath = _get_xpath(operation_elt)
        attribute = _get_text(operation_elt, 'attribute')
        return cls(xpath, attribute)


@dataclass(frozen=True)
class PatchOperationAddModExtension(PatchOperation):
    xpath: str
    value: list[etree._Element]

    def __call__(self, xml: etree._Element, _):
        found = xpath_elements(xml, self.xpath)

        for elt in found:
            mod_extensions = elt.find('modExtensions')
            if mod_extensions is None:
                mod_extensions = etree.Element('modExtensions')
                elt.append(mod_extensions)
            for v in self.value:
                mod_extensions.append(v)

    @classmethod
    def from_xml(cls, operation_elt: etree._Element) -> Self:
        xpath = _get_xpath(operation_elt)
        value = _get_value(operation_elt)
        return cls(xpath, value)


@dataclass(frozen=True)
class PatchOperationSetName(PatchOperation):
    xpath: str
    name: str

    def __call__(self, xml: etree._Element, _):
        found = xpath_elements(xml, self.xpath)

        for elt in found:
            elt.tag = self.name

    @classmethod
    def from_xml(cls, operation_elt: etree._Element) -> Self:
        xpath = _get_xpath(operation_elt)
        name = _get_text(operation_elt, 'name')
        return cls(xpath, name)


@dataclass(frozen=True)
class PatchOperationSequence(PatchOperation):
    # TODO: >  If any of them fail, then the Sequence stops and will not run any additional PatchOperations.

    operations: list[PatchOperation]

    def __call__(self, xml: etree._Element, mods: Collection[Mod]):
        for operation in self.operations:
            operation(xml, mods)

    @classmethod
    def from_xml(cls, operation_elt: etree._Element) -> Self:
        operations = collect_patches(
                _get_element(operation_elt, 'operations'),
                tag='li',
                )
        return cls(operations)


def select_operation(element: etree._Element) -> PatchOperation:
    if element.get('MayRequire') or element.get('MayRequireAnyOf'):
        return PatchOperationMeta.from_xml(element)
    return _select_operation(element)


def _select_operation(element: etree._Element) -> PatchOperation:
    class_ = element.get('Class')
    match class_:
        case 'PatchOperationAdd':
            return PatchOperationAdd.from_xml(element)
        case 'PatchOperationInsert':
            return PatchOperationInsert.from_xml(element)
        case 'PatchOperationRemove':
            return PatchOperationRemove.from_xml(element)
        case 'PatchOperationReplace':
            return PatchOperationReplace.from_xml(element)
        case 'PatchOperationAttributeAdd':
            return PatchOperationAttributeAdd.from_xml(element)
        case 'PatchOperationAttributeSet':
            return PatchOperationAttributeSet.from_xml(element)
        case 'PatchOperationAttributeRemove':
            return PatchOperationAttributeRemove.from_xml(element)
        case 'PatchOperationAddModExtension':
            return PatchOperationAddModExtension.from_xml(element)
        case 'PatchOperationSetName':
            return PatchOperationSetName.from_xml(element)
        case 'PatchOperationSequence':
            return PatchOperationSequence.from_xml(element)
        case _:
            raise MalformedPatchError(f'Unknown operation class: {class_}')


def collect_patches(xml: etree._Element, tag: str='Operation') -> list[PatchOperation]:
    result = []
    for operation_elt in xml:
        tag = operation_elt.tag
        if tag != tag:
            raise MalformedPatchError(f'Operations must be tagged as "{tag}"')
        result.append(select_operation(operation_elt))
    return result


def apply_patches(xml: etree._Element, patches: Sequence[PatchOperation], mods: Collection[Mod]|None=None):
    mods = mods or []
    for patch in patches:
        patch(xml, mods)


def get_order_append(xml: etree._Element, default: bool) -> bool:
    order_elt = xml.find('order')
    if order_elt is not None:
        if not order_elt.text or order_elt.text not in ('Prepend', 'Append'):
            raise MalformedPatchError('order should be either Append or Prepend')
        return order_elt.text == 'Append'
    return default
    

def xpath_elements(xml: etree._Element, xpath: str) -> list[etree._Element]:
    found = xml.xpath(xpath)

    if isinstance(found , etree._Element):
        found = [found]
    if not (isinstance(found, list) and all(isinstance(x, etree._Element) for x in found)):
        raise PatchError('xpath returned unexpected results')
    return cast(list[etree._Element], found)


def _get_xpath(xml: etree._Element) -> str:
    elt = xml.find('xpath')
    if elt is None:
        raise MalformedPatchError('Element not found: xpath')
    if not elt.text:
        raise MalformedPatchError('xpath element has no text')
    xpath = elt.text
    if xpath.startswith('Defs'):
        xpath = '/' + xpath
    return xpath
    
    
def _get_value(xml: etree._Element) -> list[etree._Element]:
    elt = xml.find('value')
    if elt is None:
        raise MalformedPatchError('Element not found: value')
    return list(elt)


def _get_text(xml: etree._Element, tag: str) -> str:
    elt = xml.find(tag)
    if elt is None:
        raise MalformedPatchError(f'Element not found: {tag}')
    return elt.text or ''

def _get_element(xml: etree._Element, tag: str) -> etree._Element:
    elt = xml.find(tag)
    if elt is None:
        raise MalformedPatchError(f'Element not found: {tag}')
    return elt

def unused(_):
    pass
