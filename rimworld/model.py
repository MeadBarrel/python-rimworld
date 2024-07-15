from dataclasses import MISSING, Field, dataclass, is_dataclass
from typing import Annotated, Any, Callable, Literal, Protocol, Self, Type, Union, get_args, get_origin 
from types import UnionType, NoneType
from lxml.etree import _Element, Element
from copy import deepcopy


class ModelError(Exception):
    pass


class TypeSerializer[T](Protocol):
    @classmethod
    def is_me(cls, type_, dispatch: 'Dispatch') -> Self|None:
        ...

    def value_matches(self, value) -> bool:
        ...

    def serialize(self, node: _Element, value: T):
        ...

    def deserialize(self, node: _Element) -> T:
        ...


class Dispatch(Protocol):
    def __call__(self, type_: type) -> TypeSerializer:
        ...


class BasisDispatch(Dispatch):
    def __init__(self) -> None:
        self._serializers = [
                BoolSerializer,
                IntSerializer,
                StrSerializer,
                ElementSerializer,
                ListSerializer,
                UnionSerializer,
                ModelSerializer,
                ]



    def __call__(self, type_: type) -> TypeSerializer:
        for serializer in self._serializers:
            if (result := serializer.is_me(type_, self)):
                return result
        raise ModelError(f'Cannot dispatch {type_}')


class BoolSerializer(TypeSerializer[bool]):
    @classmethod
    def is_me(cls, type_, *_) -> Self|None:
        if unannotated(type_) is bool:
            return cls()

    def value_matches(self, value) -> bool:
        return isinstance(value, bool)

    def serialize(self, node: _Element, value: bool):
        node.text = str(value).lower()

    def deserialize(self, node: _Element) -> bool:
        if node.text is None:
            raise ModelError(f'Cannot deserialize None as bool')
        
        match node.text.strip():
            case 'true':
                return True
            case 'false':
                return False
            case _:
                raise ModelError(f'Cannot deserialize {node.text.strip()[:20]} as bool')


class IntSerializer(TypeSerializer[int]):
    @classmethod
    def is_me(cls, type_, *_) -> Self|None:
        if unannotated(type_) is int:
            return cls()

    def value_matches(self, value) -> bool:
        return isinstance(value, int)

    def serialize(self, node: _Element, value: int):
        node.text = str(value)

    def deserialize(self, node: _Element) -> int:
        if node.text is None:
            raise ModelError(f'Cannot deserialize None as int')
        return int(node.text)


class StrSerializer(TypeSerializer[str]):
    @classmethod
    def is_me(cls, type_, *_) -> Self | None:
        if unannotated(type_) is str:
            return cls()

    def value_matches(self, value) -> bool:
        return isinstance(value, str)

    def serialize(self, node: _Element, value: str):
        node.text = value

    def deserialize(self, node: _Element) -> str:
        if node.text is None:
            raise ModelError(f'Cannot deserialize None as str')
        return node.text

    def union_priority(self) -> int:
        return 1


class ListSerializer[T](TypeSerializer[list[T]]):
    def __init__(self, type_: Type[T], dispatch: Dispatch) -> None:
        self._type = type_
        self._dispatch = dispatch

    @classmethod
    def is_me(cls, type_, dispatch: Dispatch) -> Self | None:
        ua = unannotated(type_)
        origin = get_origin(ua)
        if origin is not list:
            return

        args = get_args(ua)

        if len(args) != 1:
            return 

        return cls(args[0], dispatch)

    def value_matches(self, value) -> bool:
        if not isinstance(value, list):
            return False
        return all(self._dispatch(self._type).value_matches(v) for v in value)

    def serialize(self, node: _Element, value: list[T]):
        for v in value:
            n = Element('li')
            self._dispatch(self._type).serialize(n, v)
            node.append(n)

    def deserialize(self, node: _Element) -> list[T]:
        result = []
        if node.text is not None and node.text.strip():
            raise ModelError(f'list nodes cannot have text: {node.text}')
        for li in node:
            if li.tag != 'li':
                raise ModelError(f'Incorrect list tag')
            result.append(self._dispatch(self._type).deserialize(li))
        return result


class UnionSerializer(TypeSerializer[UnionType]):
    def __init__(self, types, dispatch: Dispatch):
        self._types = types
        self._dispatch = dispatch

    @classmethod
    def is_me(cls, type_, dispatch: Dispatch) -> Self | None:
        ua = unannotated(type_)
        origin = get_origin(ua)
        if origin not in (Union, UnionType):
            return
        types = get_args(ua)
        return cls(types, dispatch)

    def value_matches(self, value) -> bool:
        return any(self._dispatch(t).value_matches(value) for t in self._types)

    def serialize(self, node: _Element, value: UnionType):
        for type_ in self._types:
            if not self._dispatch(type_).value_matches(value):
                continue
            self._dispatch(type_).serialize(node, value)
            
    def deserialize(self, node: _Element) -> UnionType:
        for type_ in self._types:
            try:
                return self._dispatch(type_).deserialize(node)
            except ModelError:
                continue
        raise ModelError('Could not deserialize union')


class ElementSerializer(TypeSerializer[_Element]):
    @classmethod
    def is_me(cls, type_, *_) -> Self|None:
        if unannotated(type_) is _Element:
            return cls()

    def value_matches(self, value) -> bool:
        return isinstance(value, _Element)

    def serialize(self, node: _Element, value: _Element):
        value = deepcopy(value)
        node.text = value.text
        for k, v in value.attrib.items():
            node.set(k, v)
        for subnode in value:
            node.append(subnode)

    def deserialize(self, node: _Element) -> _Element:
        return deepcopy(node)


@dataclass
class Model:
    ...


class ModelSerializer(TypeSerializer[Model]):
    def __init__(self, type_: Model, dispatch: Dispatch):
        self._type = type_
        self._dispatch = dispatch

    @classmethod
    def is_me(cls, type_, dispatch: Dispatch) -> Self | None:
        ua = unannotated(type_)
        if not is_dataclass(ua):
            return None
        return cls(ua, dispatch)

    def value_matches(self, value) -> bool:
        return super().value_matches(value)

    def serialize(self, node: _Element, value: Model):
        for name, field in self._type.__dataclass_fields__.items():
            field: Field
            field_type = field.type
            field_name = name
            field_value = getattr(value, name)

            self._serialize_field(node, field_name, field_type, field_value)

    def _serialize_field(self, node: _Element, name: str, type_, value):
        if get_annotation(type_, Children):
            args = get_args(type_)
            assert get_origin(args[0]) is list, args
            left = [a for a in args[1:] if not isinstance(a, Children)]
            main_type = get_args(args[0])[0]
            if left:
                type_ = Annotated[main_type, *left]
            else:
                type_ = main_type
            for item in value:
                self._serialize_field(node, name, type_, item)
            return

        if _is_optional(type_):
            if value is None:
                return
            type_ = _remove_none(type_)

        if (convert := get_annotation(type_, Convert)):
            value = convert.serialize(value)

        if (alias := get_annotation(type_, Alias)):
            name = str(alias)

        if get_annotation(type_, Attr) is not None:
            node.set(name, value)
            return

        serializer = self._dispatch(type_)
        node_ = Element(name)
        serializer.serialize(node_, value)
        node.append(node_)

    def deserialize(self, node: _Element) -> Model:
        kwargs = {}
        for name, field in self._type.__dataclass_fields__.items():
            deserialized = self._deserialize_field(node, name, field)
            if deserialized is None:
                continue
            k, v = deserialized
            kwargs[k] = v
        return self._type(**kwargs)  # type: ignore


    def _deserialize_field(self, node: _Element, name: str, field: Field) -> tuple[str, Any]|None:
        field_name = name
        field_type = field.type

        if (alias:=get_annotation(field_type, Alias)) is not None:
            field_name = str(alias)


        if get_annotation(field_type, Attr) is not None:
            field_type = _remove_none(field_type)
            field_value = node.get(field_name)
            if convert := get_annotation(field_type, Convert):
                field_value = convert.deserialize(field_value)
            ua = unannotated(field_type)
            if get_origin(ua) is Literal:
                literal_value = get_args(ua)[0]
                if literal_value != field_value:
                    raise ModelError('Literal value does not match')
            return name, field_value

        if get_annotation(field_type, Children):
            args = get_args(field_type)
            assert get_origin(args[0]) is list, args
            left = [a for a in args[1:] if not isinstance(a, Children)]
            main_type = get_args(args[0])[0]
            if left:
                type_ = Annotated[main_type, *left]
            else:
                type_ = main_type
            result = []
            serializer = self._dispatch(type_)
            result = [serializer.deserialize(n) for n in node.findall(field_name)]
            return name, result

        field_node = node.find(field_name)

        if field_node is None:
            if _is_optional(field_type):
                return name, None
            if field.default is not MISSING:
                return
            if field.default_factory is not MISSING:
                return

            raise ModelError(f'Missing field: {field_name}')
        field_type = _remove_none(field_type)
        field_serializer = self._dispatch(field_type)
        return name, field_serializer.deserialize(field_node)


@dataclass(frozen=True)
class Alias:
    _alias: str
    
    def __str__(self) -> str:
        return self._alias


class Attr:
    pass


@dataclass(frozen=True)
class Convert:
    serialize: Callable
    deserialize: Callable


class Children:
    pass


def get_annotation[T](type_, annotation_type: Type[T]) -> T|None:
    if get_origin(type_) is not Annotated:
        return None
    args = get_args(type_)
    for a in args[1:]:
        if isinstance(a, annotation_type):
            return a
    return None


def unannotated(type_):
    if get_origin(type_) is not Annotated:
        return type_
    return get_args(type_)[0]


def _is_optional(type_) -> bool:
    type_ = unannotated(type_)
    if get_origin(type_) in (UnionType, Union):
        return any(x is NoneType for x in get_args(type_))
    return False


def _remove_none(type_):
    if get_origin(type_) is Annotated:
        args = get_args(type_)
        return Annotated[_remove_none(args[0]), *args[1:]]
    if get_origin(type_) not in (UnionType, Union):
        return type_
    args = [x for x in get_args(type_) if x is not NoneType]
    if len(args) > 1:
        return Union[*args]  # type: ignore
    return args[0]

