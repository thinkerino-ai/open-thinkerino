import pickle

from aitools.logic import Expression
from aitools.logic.utils import constants, expr


# TODO this test is just a canary to detect the moment I start working on IDs to remind me to remove pickling
#  customization
def test_expression_ids_exist():
    a, b = constants('a, b')
    e1: Expression = expr(a, b)

    assert hasattr(e1, 'id')
    assert isinstance(e1.id, int)


def test_expression_pickling_works():
    a, b = constants('a, b')
    e1: Expression = expr(a, b)

    assert hasattr(e1, 'id')

    pickled = pickle.dumps(e1)
    unpickled: Expression = pickle.loads(pickled)

    assert unpickled is not e1
    assert unpickled.id == -1
    assert unpickled == e1