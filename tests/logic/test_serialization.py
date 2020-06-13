import pickle

from aitools.logic.core import Expression
from aitools.logic.utils import constants, expr


def test_expression_pickling_works():
    a, b = constants('a, b')
    e1: Expression = expr(a, b)

    pickled = pickle.dumps(e1)
    unpickled: Expression = pickle.loads(pickled)

    assert unpickled is not e1
    assert unpickled == e1