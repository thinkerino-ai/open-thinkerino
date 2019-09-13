from aitools.logic import Substitution
from aitools.logic.utils import expr, logic_objects, subst


def test_logic_object_invocation():
    a, b, c, d = logic_objects(4)

    e1 = expr(a, b, c, d)
    e2 = a(b, c, d)

    assert e1 == e2


def test_variable_source():
    from aitools.logic.utils import variable_source as v
    a, b, c, d = logic_objects(4)

    e1 = expr(a, (b, c), (v.x, b, d))
    e2 = expr(a, (v.x, c), (v.y, v.x, d))

    expected_result = subst((b, [v.x, v.y]))

    result = Substitution.unify(e1, e2)

    assert result == expected_result, \
        f"Unification between {e1} and {e2} should give {expected_result}, got {result} instead"
