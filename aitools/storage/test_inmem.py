import pytest

from aitools.logic import Constant, Variable, Expression, LogicWrapper, LogicObject
from aitools.storage.inmem import InMemLogicObjectStorage


@pytest.fixture(params=[
    Constant(),
    Variable(),
    Expression(Constant(), Variable(), Expression(Constant(), Constant())),
    LogicWrapper(("A", "very", "nice", 2, "ple"))
])
def single_logic_object(request) -> LogicObject:
    return request.param


def test_logic_object_storage_store_and_retrieve(single_logic_object: LogicObject):
    storage = InMemLogicObjectStorage()

    storage.add(single_logic_object)

    res = storage.get_by_id(single_logic_object.id)

    assert res is not single_logic_object
    assert res == single_logic_object

