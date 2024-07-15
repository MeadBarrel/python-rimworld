from dataclasses import dataclass, field
from typing import Annotated, Literal
from lxml import etree
from pytest import fixture
import pytest
from rimworld.model import Alias, Dispatch, BasisDispatch, Attr, Convert, Children, ModelError


@fixture
def dispatch() -> Dispatch:
    return BasisDispatch()

@fixture
def node() -> etree._Element:
    return etree.Element('node')


def test_serialize_bool_true(node: etree._Element, dispatch: Dispatch):
    dispatch(bool).serialize(node, True)
    assert node.text == 'true'


def test_deserialize_bool_true(node: etree._Element, dispatch: Dispatch):
    node.text = '  true '
    assert dispatch(bool).deserialize(node) is True


def test_deserialize_bool_false(node: etree._Element, dispatch: Dispatch):
    node.text = ' false '
    assert dispatch(bool).deserialize(node) is False


def test_serialize_bool_false(node: etree._Element, dispatch: Dispatch):
    dispatch(bool).serialize(node, False)
    assert node.text == 'false'


def test_serialize_int(node: etree._Element, dispatch: Dispatch):
    dispatch(int).serialize(node, 5)
    assert node.text == '5'


def test_deserialise_int(node: etree._Element, dispatch: Dispatch):
    node.text = ' 9'
    assert dispatch(int).deserialize(node) == 9


def test_serialize_str(node: etree._Element, dispatch: Dispatch):
    dispatch(str).serialize(node, 'value')
    assert node.text == 'value'

def test_deserialize_str(node: etree._Element, dispatch: Dispatch):
    node.text = '  value '
    assert dispatch(str).deserialize(node) == '  value '


@pytest.mark.parametrize(
        ('type_', 'values', 'expected'),
        [
            (list[str], ['a', 'b', 'c'], ['a', 'b', 'c']),
            (list[int], [9, 8], ['9', '8']),
            (list[bool], [True, False, True], ['true', 'false', 'true'])
        ]
        )
def test_serialize_list(
        node: etree._Element, 
        dispatch: Dispatch, 
        type_, 
        values: list, 
        expected: list[str]
        ):
    dispatch(type_).serialize(node, values)
    assert len(node) == len(expected)
    for li, ev in zip(node, expected):
        assert li.tag == 'li'
        assert li.text == ev


@pytest.mark.parametrize(
        ('type_', 'values', 'expected'),
        [
            (list[str], ['1', '2', '3'], ['1', '2', '3']),
            (list[int], ['1', ' 2', '   3 '], [1, 2, 3]),
            (list[bool], ['true', ' false \n', 'true '], [True, False, True])
        ]
        )
def test_deserialize_list(
        node: etree._Element, 
        dispatch: Dispatch, 
        type_, 
        values: list[str], 
        expected: list
        ):
    for v in values:
        n = etree.Element('li')
        n.text = v
        node.append(n)
    result = dispatch(type_).deserialize(node)
    assert len(result) == len(expected)
    for r, ev in zip(result, expected):
        assert r == ev


def test_serialize_list_nested(dispatch: Dispatch):
    xml_raw = '''
    <node>
        <li>
            <li>1</li>
            <li>2</li>
        </li>
        <li>
            <li>3</li>
            <li>4</li>
        </li>
    </node>
    '''
    xml = etree.fromstring(xml_raw)
    result = dispatch(list[list[int]]).deserialize(xml)
    assert result == [[1, 2], [3, 4]]


def test_deserialize_list_nested(node: etree._Element, dispatch: Dispatch):
    xml_raw = '''
    <node>
        <li>
            <li>1</li>
            <li>2</li>
        </li>
        <li>
            <li>3</li>
            <li>4</li>
        </li>
    </node>
    '''
    expected = etree.fromstring(xml_raw)
    value = [[1, 2], [3, 4]]
    dispatch(list[list[int]]).serialize(node, value)

    assert_xml_eq(node, expected)


@pytest.mark.parametrize(
        ('type_', 'value', 'xml'),
        [
            (list[str]|str|list[bool], 'abc', '<node>abc</node>'),
            (list[str]|str|list[bool], [True, False], '<node><li>true</li><li>false</li></node>'),
            (list[str]|str|list[bool], ['a', 'b'], '<node><li>a</li><li>b</li></node>'),
        ]
        )
def test_serialize_union(
        node: etree._Element, 
        dispatch: Dispatch,
        type_,
        value,
        xml: str,
        ):
    expected = etree.fromstring(xml)
    dispatch(type_).serialize(node, value)
    assert_xml_eq(node, expected)


@pytest.mark.parametrize(
        ('type_', 'xml', 'value'),
        [
            (list[str]|str|list[bool], '<node>abc</node>', 'abc'),
            (str|list[bool]|list[str], '<node><li>true</li><li>false</li></node>', [True, False]),
            (list[str]|list[list[int]]|list[bool], '<node><li><li>1</li><li>2</li></li></node>', [[1, 2]])
        ]
        )
def test_deserialize_union(
        dispatch: Dispatch,
        type_,
        xml: str,
        value
        ):
    node = etree.fromstring(xml)
    result = dispatch(type_).deserialize(node)
    assert result == value



def test_serialize_element(node: etree._Element, dispatch: Dispatch):
    elt_raw = '<something attrib="1"><some>text</some></something>'
    expected_raw = f'<node attrib="1"><some>text</some></node>'
    elt = etree.fromstring(elt_raw)
    expected = etree.fromstring(expected_raw)
    dispatch(etree._Element).serialize(node, elt)
    assert_xml_eq(node, expected)


def test_deserialize_element(dispatch: Dispatch):
    elt_raw = '<something><some>text</some></something>'
    value = etree.fromstring(elt_raw)
    expected = etree.fromstring(elt_raw)
    result = dispatch(etree._Element).deserialize(value)
    assert_xml_eq(result, expected)
    

def test_serialize_model(node: etree._Element, dispatch: Dispatch):
    @dataclass(kw_only=True)
    class SimpleModel:
        child_list: Annotated[list[str], Children(), Alias('child')]
        attribute: Annotated[str, Attr()]
        attribute_aliased: Annotated[str, Attr(), Alias('atal')]
        attribute_none2: Annotated[str|None, Attr()]= None
        attribute_maybe_str: Annotated[str|None, Attr()] = 'ams'
        attribute_list: Annotated[
                list[str], 
                Attr(), 
                Convert(lambda x: ','.join(x), lambda x: x.split(','))
                ]
        list_of_strings: list[str]
        bool_or_int: bool|int = True
        optional: int|None
        aliased: Annotated[str, Alias('ALIASED')]

    value = SimpleModel(
            child_list=['a', 'b', 'c'],
            attribute='attribute value',
            attribute_aliased='atal value',
            attribute_list=['a', 'b', 'c'],
            list_of_strings=['a', 'b'], 
            bool_or_int=3, 
            optional=None,
            aliased='aliased value'
            )
    expected_raw = '''
    <node attribute="attribute value" attribute_list="a,b,c" attribute_maybe_str="ams" atal="atal value">
        <child>a</child>
        <child>b</child>
        <child>c</child>
        <list_of_strings>
            <li>a</li>
            <li>b</li>
        </list_of_strings>
        <bool_or_int>3</bool_or_int>
        <ALIASED>aliased value</ALIASED>
    </node>
    '''
    expected = etree.fromstring(expected_raw)

    dispatch(SimpleModel).serialize(node, value)
    assert_xml_eq(node, expected)


def test_deserialize_model(dispatch: Dispatch):
    @dataclass(kw_only=True)
    class SimpleModel:
        child_list: Annotated[list[str], Children(), Alias('child')]
        attribute: Annotated[str, Attr()]
        attribute_aliased: Annotated[str, Attr(), Alias('atal')]
        attribute_maybe_str: Annotated[str|None, Attr()]
        # note:  attribute_maybe_str: Annotated[str, Attr()]|None doesn't work
        attribute_list: Annotated[
                list[str], 
                Attr(), 
                Convert(lambda x: ','.join(x), lambda x: x.split(','))
                ]
        list_of_strings: list[str]
        bool_or_int: bool|int
        number: int = 7
        factory_number: list[str] = field(default_factory=list)
        aliased: Annotated[str, Alias('ALIASED')]
        optional: int|None

    raw = '''
    <node attribute="attribute value" attribute_list="a,b,c" attribute_maybe_str="ams" atal="atal value">
        <child>a</child>
        <child>b</child>
        <child>c</child>
        <list_of_strings>
            <li>a</li>
            <li>b</li>
        </list_of_strings>
        <bool_or_int>3</bool_or_int>
        <ALIASED>aliased value</ALIASED>
    </node>
    '''
    node = etree.fromstring(raw)
    expected_value = SimpleModel(
            child_list=['a', 'b', 'c'],
            attribute='attribute value',
            attribute_aliased='atal value',
            attribute_maybe_str='ams',
            attribute_list=['a', 'b', 'c'],
            list_of_strings=['a', 'b'], 
            bool_or_int=3,
            optional=None,
            aliased='aliased value'
            )
    result = dispatch(SimpleModel).deserialize(node)
    assert result == expected_value


def test_serialize_model_literal_attr(node: etree._Element, dispatch: Dispatch):
    @dataclass(kw_only=True)
    class SimpleModel:
        literal: Annotated[Literal['tag'], Attr()]
        some_value: int

    value = SimpleModel(literal='tag', some_value=5)

    raw = '''
    <node literal="tag"><some_value>5</some_value></node>
    '''
    expected = etree.fromstring(raw)
    dispatch(SimpleModel).serialize(node, value)
    assert_xml_eq(node, expected)


def test_deserialize_model_literal_attr(node: etree._Element, dispatch: Dispatch):
    @dataclass(kw_only=True)
    class SimpleModel:
        literal: Annotated[Literal['tag'], Attr()]
        some_value: int

    expected = SimpleModel(literal='tag', some_value=5)

    raw = '''
    <node literal="tag"><some_value>5</some_value></node>
    '''
    node = etree.fromstring(raw)
    value = dispatch(SimpleModel).deserialize(node)
    assert value == expected

def test_deserialize_model_literal_attr_fails(node: etree._Element, dispatch: Dispatch):
    @dataclass(kw_only=True)
    class SimpleModel:
        literal: Annotated[Literal['tag'], Attr()]
        some_value: int

    raw = '''
    <node attribute="wrong tag"><some_value>5</some_value></node>
    '''
    node = etree.fromstring(raw)
    with pytest.raises(ModelError):
        dispatch(SimpleModel).deserialize(node)


def test_deserialize_model_literal_attr_fails_notpresent(node: etree._Element, dispatch: Dispatch):
    @dataclass(kw_only=True)
    class SimpleModel:
        literal: Annotated[Literal['tag'], Attr()]
        some_value: int

    raw = '''
    <node><some_value>5</some_value></node>
    '''
    node = etree.fromstring(raw)
    with pytest.raises(ModelError):
        dispatch(SimpleModel).deserialize(node)


def assert_xml_eq(e1: etree._Element, e2: etree._Element, path=''):
    if not isinstance(e1, etree._Element):
        raise AssertionError(f'e1 ({e1}) is {type(e1)}, not _Element')
    if not isinstance(e2, etree._Element):
        raise AssertionError(f'e2 ({e2}) is {type(e2)}, not _Element')

    # Compare tags

    if e1.tag != e2.tag:
        raise AssertionError(f"Tags do not match at {path}: {e1.tag} != {e2.tag}")
    
    # Compare text
    if (e1.text or '').strip() != (e2.text or '').strip():
        raise AssertionError(f"Text does not match at {path}: '{e1.text}' != '{e2.text}'")
    
    # Compare tails
    if (e1.tail or '').strip() != (e2.tail or '').strip():

        raise AssertionError(f"Tails do not match at {path}: '{e1.tail}' != '{e2.tail}'")
    
    # Compare attributes
    if e1.attrib != e2.attrib:
        raise AssertionError(f"Attributes do not match at {path}: {e1.attrib} != {e2.attrib}")
    
    # Compare children
    if len(e1) != len(e2):
        print('NOMATCH')
        print(str(etree.tostring(e1, pretty_print=True)))
        print(str(etree.tostring(e2, pretty_print=True)))
        raise AssertionError(f"Number of children do not match at {path}: {len(e1)} != {len(e2)}")
    
    # Recursively compare children
    for i, (c1, c2) in enumerate(zip(e1, e2)):
        assert_xml_eq(c1, c2, path=f"{path}/{e1.tag}[{i}]")

