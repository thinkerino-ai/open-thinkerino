import uuid

from aitools.logic.core import Constant
from aitools.logic.language import Language
from aitools.logic.utils import constants, expr, binding, variables


def test_expression_equality_success():
    language = Language()
    a, b, c, d = constants('a, b, c, d', language=language)

    e1 = expr(a, (b, c), d)
    e2 = expr(a, (b, c), d)

    assert e1 == e2, f"{e1} and {e2} should be equal!"


def test_expression_equality_failure():
    language = Language()
    a, b, c, d = constants('a, b, c, d', language=language)

    e1 = expr(a, (b, c), d)
    e2 = expr(a, (b, c), a)

    assert e1 != e2, f"{e1} and {e2} should not be equal!"


def test_different_language_equality_failure():
    language_1 = Language(language_id=uuid.UUID(int=1), next_id=0)
    language_2 = Language(language_id=uuid.UUID(int=2), next_id=0)

    a_1 = Constant(name="a", language=language_1)
    a_2 = Constant(name="a", language=language_2)

    assert a_1 != a_2


def test_binding_equality_success_with_head():
    language = Language()
    a = Constant(name='a', language=language)

    v1, v2, v3 = variables('v1, v2, v3', language=language)

    b1 = binding(a, [v1, v2, v3])
    b2 = binding(a, [v3, v2, v1])

    assert b1 == b2


def test_binding_equality_success_without_head():
    language = Language()
    v1, v2, v3 = variables('v1, v2, v3', language=language)

    b1 = binding(None, [v1, v2, v3])
    b2 = binding(None, [v2, v3, v1])

    assert b1 == b2


def test_binding_equality_failure_variables():
    language = Language()
    a = Constant(name='a', language=language)

    v1, v2, v3 = variables('v1, v2, v3', language=language)

    b1 = binding(a, [v1, v2, v3])
    b2 = binding(a, [v2, v1])

    assert b1 != b2


def test_binding_equality_failure_head():
    language = Language()
    a, b = constants('a, b', language=language)

    v1, v2 = variables('v1, v2', language=language)

    b1 = binding(a, [v1, v2])
    b2 = binding(b, [v2, v1])

    assert b1 != b2
