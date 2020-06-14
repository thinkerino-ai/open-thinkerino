import uuid
from typing import Optional

import pytest

from aitools.logic.core import Variable, LogicObject
from aitools.logic.language import Language
from aitools.logic.unification import Substitution, Binding, UnificationError
from aitools.logic.utils import constants, expr, variables, subst, binding, wrap


def assert_unification_result(e1: LogicObject, e2: LogicObject, expected_result: Optional[Substitution], *,
                              previous: Substitution = None):
    result = Substitution.unify(e1, e2, previous=previous)
    if expected_result is not None:
        assert result is not None
    assert result == expected_result, f"Unification between {e1} and {e2} should give {expected_result}, got {result} " \
                                      f"instead"


def test_binding_join():
    language = Language()
    x, y, z = variables('x, y, z', language=language)
    a, b = constants('a, b', language=language)

    h1 = expr(z)
    h2 = expr(b)

    b1 = Binding(frozenset([x]), h1)
    b2 = Binding(frozenset([y]), h2)

    try:
        assert Binding.join(b1, b2).head == h2
    except UnificationError as e:
        pytest.fail(str(e))


def test_unification_between_logic_objects_failure():
    language = Language()
    a, b = constants('a, b', language=language)

    assert_unification_result(a, b, None)


def test_unification_between_logic_objects_success():
    language = Language()
    a, = constants('a', language=language)

    expected_result = subst()
    assert_unification_result(a, a, expected_result)


def test_unification_between_expressions_success():
    language = Language()
    a, b, c, d = constants('a, b, c, d', language=language)
    e1 = expr(a, (b, c), d)
    e2 = expr(a, (b, c), d)

    expected_result = subst()
    assert_unification_result(e1, e2, expected_result)


def test_unification_between_expressions_failure():
    language = Language()
    a, b, c, d = constants('a, b, c, d', language=language)
    e1 = expr(a, (b, c), d)
    e2 = expr(a, (b, c), a)

    assert_unification_result(e1, e2, None)


def test_unification_with_variables_success_simple():
    language = Language()
    v1, = variables('v1', language=language)
    a, b, c, d = constants('a, b, c, d', language=language)

    expr_d = expr([d])
    e1 = expr(a, (b, c), expr_d)

    expected_result = subst((e1, [v1]))

    assert_unification_result(v1, e1, expected_result)


def test_unification_with_variables_across_languages():
    v1, = variables('v1', language=Language(language_id=uuid.UUID(int=0), next_id=0))
    a, b, c, d = constants('a, b, c, d', language=Language(language_id=uuid.UUID(int=1), next_id=0))

    expr_d = expr([d])
    e1 = expr(a, (b, c), expr_d)

    expected_result = subst((e1, [v1]))

    assert_unification_result(v1, e1, expected_result)


def test_unification_with_variables_success_complex():
    language = Language()
    v1, v2 = variables('v1, v2', language=language)
    a, b, c, d = constants('a, b, c, d', language=language)

    expr_d = expr([d])
    e1 = expr(a, (b, c), expr_d)
    e2 = expr(a, (v1, c), v2)

    expected_result = subst((b, [v1]), (expr_d, [v2]))

    assert_unification_result(e1, e2, expected_result)


def test_unification_with_variables_failure_conflict():
    language = Language()
    v1, = variables('v1', language=language)
    a, b, c, d = constants('a, b, c, d ', language=language)

    expr_d = expr([d])
    e1 = expr(a, (b, c), expr_d)
    e3 = expr(a, (v1, c), v1)

    assert_unification_result(e1, e3, None)


def test_unification_with_variables_success_equality():
    language = Language()
    v1, v2 = variables('v1, v2', language=language)
    a, c = constants('a, c', language=language)

    e2 = expr(a, (v1, c), v2)
    e3 = expr(a, (v1, c), v1)

    expected_result = subst((None, [v1, v2]))

    assert_unification_result(e2, e3, expected_result)


def test_unification_with_variables_failure_contained():
    language = Language()
    v1, v2 = variables('v1, v2', language=language)
    a, c, d = constants('a, c, d', language=language)

    expr_d = expr([d])
    e2 = expr(a, (v1, c), v2)
    e4 = expr(a, v1, expr_d)

    assert_unification_result(e2, e4, None)


def test_unification_with_variables_success_same_expression():
    language = Language()
    v1, v2 = variables('v1, v2', language=language)
    a, b, c, d = constants('a, b, c, d', language=language)

    bc_expr1 = expr(b, c)
    bc_expr2 = expr(b, c)
    e1 = expr(a, bc_expr1, v1, d)
    e2 = expr(a, v2, bc_expr2, d)

    expected_result = subst((bc_expr1, [v1]), (bc_expr2, [v2]))

    assert_unification_result(e1, e2, expected_result)


def test_unification_with_previous_simple_succeeding():
    language = Language()
    x = Variable(name='x', language=language)
    a, b, c, d = constants('a, b, c, d', language=language)

    bc_expr = expr(b, c)
    e1 = expr(a, bc_expr, d)
    e2 = expr(a, x, d)

    previous = subst((bc_expr, [x]))

    assert_unification_result(e1, e2, previous, previous=previous)


def test_unification_with_previous_simple_failing():
    language = Language()
    x = Variable(name='x', language=language)
    a, b, c, d = constants('a, b, c, d', language=language)

    bc_expr = expr(b, c)
    e1 = expr(a, bc_expr, d)
    e2 = expr(a, x, d)

    previous = subst((b, [x]))

    assert_unification_result(e1, e2, None, previous=previous)


def test_unification_with_previous_success_bound_to_same_expression():
    language = Language()
    x, y, z = variables('x, y, z', language=language)
    a, d = constants('a, d', language=language)

    e2 = expr(a, x, z)
    e3 = expr(a, y, d)

    previous = subst((a, [x]), (a, [y]))

    expected_result = previous.with_bindings(binding(d, [z]))

    assert_unification_result(e2, e3, expected_result, previous=previous)


def test_unification_with_previous_success_bound_to_unifiable_expressions():
    language = Language()
    x, y, z = variables('x, y, z', language=language)
    a, b, c, d = constants('a, b, c, d', language=language)

    bc_expr = expr(b, c)
    bz_expr = expr(b, z)
    e2 = expr(a, x, d)
    e3 = expr(a, y, d)

    previous = subst((bc_expr, [x]), (bz_expr, [y]))

    expected_result = previous.with_bindings(binding(c, [z]))

    assert_unification_result(e2, e3, expected_result, previous=previous)


def test_unification_with_previous_failure_bound_to_different_expressions():
    language = Language()
    x, y = variables('x, y', language=language)
    a, b, d = constants('a, b, d', language=language)

    e2 = expr(a, x, d)
    e3 = expr(a, y, d)

    previous = subst((a, [x]), (b, [y]))

    assert_unification_result(e2, e3, None, previous=previous)


def test_unification_with_previous():
    language = Language()
    w, x, y, z = variables('w, x, y, z', language=language)
    a, d = constants('a, d', language=language)

    e2 = expr(a, x, d)
    e3 = expr(a, y, d)

    previous = subst((None, [x, z]), (None, [y, w]))

    expected_result = subst((None, [w, x, y, z]))

    assert_unification_result(e2, e3, expected_result, previous=previous)


def test_unification_with_repeated_constants():
    language = Language()
    v1 = Variable(name='x', language=language)

    e1 = expr(2, v1)
    e2 = expr(2, "hi")

    expected_result = subst((wrap("hi"), [v1]))
    assert_unification_result(e1, e2, expected_result)


def test_unification_weird_failing_case():
    language = Language()
    v1, v2 = variables('v1, v2', language=language)
    c, d = constants('c, d', language=language)
    e1 = expr("hello", ("yay", c), [d])
    e2 = expr("hello", (v1, c), v2)

    expected_result = subst((wrap("yay"), [v1]), (expr(d), [v2]))

    assert_unification_result(e1, e2, expected_result)
