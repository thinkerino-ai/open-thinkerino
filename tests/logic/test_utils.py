from aitools.logic.utils import expr, logicObjects


def test_logic_object_invocation():
    a, b, c, d = logicObjects()

    e1 = (a, b, c, d) >> expr
    e2 = a(b, c, d)

    assert e1 == e2