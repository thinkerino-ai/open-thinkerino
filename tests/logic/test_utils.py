from aitools.logic import Substitution
from aitools.logic.utils import expr, logic_objects, subst, VariableSource, renew_variables


def test_logic_object_invocation():
    a, b, c, d = logic_objects(4)

    e1 = expr(a, b, c, d)
    e2 = a(b, c, d)

    assert e1 == e2


def test_variable_source():
    v = VariableSource()
    a, b, c, d = logic_objects(4)

    e1 = expr(a, (b, c), (v.x, b, d))
    e2 = expr(a, (v.x, c), (v.y, v.x, d))

    expected_result = subst((b, [v.x, v.y]))

    result = Substitution.unify(e1, e2)

    assert result == expected_result, \
        f"Unification between {e1} and {e2} should give {expected_result}, got {result} instead"


def test_renew_variables():
    v = VariableSource()
    a, b, c = logic_objects(3)
    e1 = expr(v.x, v.y, v.x)
    e2 = renew_variables(e1)

    assert e2.children[0] != e2.children[1]
    assert e2.children[0] == e2.children[2]


def test_renew_variables_preserves_unification():
    v = VariableSource()
    a, b, c, d = logic_objects(4)

    e1 = expr(v.x, (v.y, v.z), d)
    e2 = renew_variables(e1)

    e3 = expr(a, (b, c), d)

    unifier1 = Substitution.unify(e1, e3)
    unifier2 = Substitution.unify(e2, e3)

    unified1 = unifier1.apply_to(e1)
    unified2 = unifier2.apply_to(e2)

    assert unifier1 != unifier2
    assert unified1 == unified2