from collections import namedtuple

import pytest

from aitools.logic.utils import constants, VariableSource, normalize_variables
from aitools.storage.base import LogicObjectStorage
from aitools.storage.inmem import InMemSerializingLogicObjectStorage

StorageFactory = namedtuple("StorageFactory", ["factory", "preserves_identity"])


@pytest.fixture(params=[
    StorageFactory(factory=InMemSerializingLogicObjectStorage, preserves_identity=False)
])
def storage_factory(request):
    return request.param


def test_retrieve_known_formula(storage_factory):
    factory, preserves_identity = storage_factory
    storage: LogicObjectStorage = factory()

    IsA, dylan, cat = constants('IsA, dylan, cat')

    storage.add(IsA(dylan, cat))

    # we can retrieve it because we already know it
    retrieved = set(storage.search_unifiable(IsA(dylan, cat)))

    assert retrieved == {IsA(dylan, cat)}


def test_retrieve_known_open_formula(storage_factory):
    factory, preserves_identity = storage_factory
    storage: LogicObjectStorage = factory()

    v = VariableSource()

    IsA, dylan, cat, hugo = constants('IsA, dylan, cat, hugo')

    storage.add(
        IsA(dylan, cat),
        IsA(hugo, cat)
    )

    retrieved = set(storage.search_unifiable(IsA(v._x, cat)))
    assert retrieved == {IsA(dylan, cat), IsA(hugo, cat)}


def test_normalized_formulas_added_only_once(storage_factory):
    factory, preserves_identity = storage_factory
    storage: LogicObjectStorage = factory()

    v = VariableSource()
    Foo, a, b = constants('Foo, a, b')

    normalizer = VariableSource()
    storage.add(*(
        normalize_variables(x, variable_source=normalizer)
        for x in (Foo(a, b), Foo(v.x, v.y), Foo(v.x, v.x), Foo(v.w, v.z))
    ))

    assert len(storage) == 3