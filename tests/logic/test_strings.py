import uuid

from aitools.logic.core import Constant, Variable, Expression, LogicWrapper
from aitools.logic.language import Language


def _do_test_symbol_representation(*, function, symbol_class, name, next_id, result):
    language = Language()
    language._id = uuid.UUID(int=0)
    language._next_id = next_id
    symbol = symbol_class(name=name, language=language)
    assert function(symbol) == result


def test_constant_str__no_name():
    _do_test_symbol_representation(function=str, symbol_class=Constant, name=None, next_id=33, result="o33")


def test_constant_str__with_name():
    _do_test_symbol_representation(function=str, symbol_class=Constant, name="foo", next_id=33, result="foo33")


def test_variable_str__no_name():
    _do_test_symbol_representation(function=str, symbol_class=Variable, name=None, next_id=33, result="?v33")


def test_variable_str__with_name():
    _do_test_symbol_representation(function=str, symbol_class=Variable, name="foo", next_id=33, result="?foo33")


def test_constant_repr__no_name():
    _do_test_symbol_representation(
        function=repr, symbol_class=Constant, name=None, next_id=33,
        result="Constant(name=None, id=Identifier(language=Language(language_id=UUID("
               "'00000000-0000-0000-0000-000000000000'), next_id=0), sequential_id=33))")


def test_constant_repr__with_name():
    _do_test_symbol_representation(
        function=repr, symbol_class=Constant, name="foo", next_id=33,
        result="Constant(name='foo', id=Identifier(language=Language(language_id=UUID("
               "'00000000-0000-0000-0000-000000000000'), next_id=0), sequential_id=33))")


def test_variable_repr__no_name():
    _do_test_symbol_representation(
        function=repr, symbol_class=Variable, name=None, next_id=33,
        result="Variable(name=None, id=Identifier(language=Language(language_id=UUID("
               "'00000000-0000-0000-0000-000000000000'), next_id=0), sequential_id=33))")


def test_variable_repr__with_name():
    _do_test_symbol_representation(
        function=repr, symbol_class=Variable, name="foo", next_id=33,
        result="Variable(name='foo', id=Identifier(language=Language(language_id=UUID("
               "'00000000-0000-0000-0000-000000000000'), next_id=0), sequential_id=33))")


def test_expression_str():
    language = Language()
    language._id = uuid.UUID(int=0)
    language._next_id = 33
    expr = Expression(
        Constant(name='a', language=language), Constant(name='b', language=language),
        Expression(Constant(name='c', language=language))
    )
    assert str(expr) == '(a33, b34, (c35))'


def test_expression_repr():
    language = Language()
    language._id = uuid.UUID(int=0)
    language._next_id = 33
    expr = Expression(
        Constant(name='a', language=language), Constant(name='b', language=language),
        Expression(Constant(name='c', language=language))
    )
    assert repr(expr) == "Expression(" \
                         "(Constant(name='a', id=Identifier(language=Language(language_id=UUID(" \
                         "'00000000-0000-0000-0000-000000000000'), next_id=0), sequential_id=33)), " \
                         "Constant(name='b', id=Identifier(language=Language(language_id=UUID(" \
                         "'00000000-0000-0000-0000-000000000000'), next_id=0), sequential_id=34)), " \
                         "Expression((Constant(name='c', id=Identifier(language=Language(language_id=UUID(" \
                         "'00000000-0000-0000-0000-000000000000'), next_id=0), sequential_id=35)),))))"


def test_logic_wrapper_str():
    wrapper = LogicWrapper("foo")
    assert str(wrapper) == "{foo}"


def test_logic_wrapper_repr():
    wrapper = LogicWrapper("foo")
    assert repr(wrapper) == "LogicWrapper('foo')"

