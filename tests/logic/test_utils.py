import pytest

from aitools.logic import Substitution, Variable, LogicObject, Constant
from aitools.logic.utils import expr, constants, subst, VariableSource, normalize_variables, all_unique_variables_in, \
    all_variables_in, map_variables_by_name


def test_logic_object_invocation():
    a, b, c, d = constants('a, b, c, d')

    e1 = expr(a, b, c, d)
    e2 = a(b, c, d)

    assert e1 == e2


def test_variable_source_getattr():
    v = VariableSource()

    assert v.x == v['x']

    a, b, c, d = constants('a, b, c, d')

    e1 = expr(a, (b, c), (v.x, b, d))
    e2 = expr(a, (v.x, c), (v.y, v.x, d))

    expected_result = subst((b, [v.x, v.y]))

    result = Substitution.unify(e1, e2)

    assert result == expected_result, \
        f"Unification between {e1} and {e2} should give {expected_result}, got {result} instead"


def test_normalize_variables():
    v = VariableSource()
    a, b, c = constants('a, b, c')
    e1 = expr(v.x, v.y, v.x)
    e2, mapping = normalize_variables(e1)

    assert e2.children[0] != e2.children[1]
    assert e2.children[0] == e2.children[2]

    assert mapping[v.x] == e2.children[0]
    assert mapping[v.y] == e2.children[1]


def test_normalize_variables_preserves_unification():
    v = VariableSource()
    a, b, c, d = constants('a, b, c, d')

    e1 = expr(v.x, (v.y, v.z), d)
    e2, _ = normalize_variables(e1)

    e3 = expr(a, (b, c), d)

    unifier1 = Substitution.unify(e1, e3)
    unifier2 = Substitution.unify(e2, e3)

    unified1 = unifier1.apply_to(e1)
    unified2 = unifier2.apply_to(e2)

    assert unifier1 != unifier2
    assert unified1 == unified2


def test_normalize_variables_with_source_makes_expressions_equal():
    v = VariableSource()
    norm = VariableSource()

    e1 = expr(v.x, (v.y, v.z))
    e2 = expr(v.z, (v.x, v.y))
    e3 = expr(v.z, (v.y, v.x))
    e4 = expr(v.a, (v.b, v.c))
    e_diff = expr(v.q, (v.q, v.q))

    assert e1 != e2
    assert e1 != e3
    assert e1 != e4
    assert e1 != e_diff

    assert normalize_variables(e1, variable_source=norm)[0] == normalize_variables(e2, variable_source=norm)[0]
    assert normalize_variables(e1, variable_source=norm)[1] != normalize_variables(e2, variable_source=norm)[1]
    assert normalize_variables(e1, variable_source=norm)[0] == normalize_variables(e3, variable_source=norm)[0]
    assert normalize_variables(e1, variable_source=norm)[1] != normalize_variables(e3, variable_source=norm)[1]
    assert normalize_variables(e1, variable_source=norm)[0] == normalize_variables(e4, variable_source=norm)[0]
    assert normalize_variables(e1, variable_source=norm)[1] != normalize_variables(e4, variable_source=norm)[1]
    assert normalize_variables(e1, variable_source=norm)[0] != normalize_variables(e_diff, variable_source=norm)[0]
    assert normalize_variables(e1, variable_source=norm)[1] != normalize_variables(e_diff, variable_source=norm)[1]


def test_all_variables_in_single_variable():
    v = Variable()
    res = list(all_variables_in(v))

    assert res == [v]


def test_all_variables_in_logic_object_is_empty():
    obj = LogicObject()
    res = list(all_variables_in(obj))

    assert len(res) == 0


def test_all_variables_in_expression():
    v = VariableSource()
    a = Constant()
    e1 = expr(v.x, (v.y, v.z), (a, v.x))

    res = list(all_variables_in(e1))

    assert res == [v.x, v.y, v.z, v.x]


def test_all_unique_variables_in_expression():
    v = VariableSource()
    a = Constant()
    e1 = expr(v.x, (v.y, v.z), (a, v.x))

    res = all_unique_variables_in(e1)

    assert res == {v.x, v.y, v.z}


def test_map_variables_by_name_success():
    v = VariableSource()
    a = Constant()
    e1 = expr(v.x, (v.y, v.z), (a, v.x))

    res = map_variables_by_name(e1)

    assert res == dict(x=v.x, y=v.y, z=v.z)


def test_map_variables_by_name_homonymous_failure():
    v1 = VariableSource()
    v2 = VariableSource()
    a = Constant()
    e1 = expr(v1.x, (v1.y, v1.z), (a, v2.x))

    with pytest.raises(ValueError):
        map_variables_by_name(e1)