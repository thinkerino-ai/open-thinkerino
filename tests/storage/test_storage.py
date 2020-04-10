from dataclasses import dataclass
from typing import Callable

import pytest

from aitools.logic.utils import constants, VariableSource, normalize_variables
from aitools.storage.base import LogicObjectStorage
from aitools.storage.dummy import DummyLogicObjectStorage, DummyIndexedLogicObjectStorage
from aitools.storage.inmem_serializing import InMemSerializingLogicObjectStorage, \
    DummyIndexedSerializingLogicObjectStorage


@dataclass
class StorageImplementation:
    storage_factory: Callable[[], LogicObjectStorage]
    preserves_identity: bool

@pytest.fixture(
    params=[
        StorageImplementation(DummyLogicObjectStorage, True),
        StorageImplementation(InMemSerializingLogicObjectStorage, False),
        StorageImplementation(DummyIndexedLogicObjectStorage, True),
        StorageImplementation(DummyIndexedSerializingLogicObjectStorage, False)
    ])
def storage_implementation(request):
    """Each param is a pair of a storage factory and a boolean which says if it preserves identity"""
    return request.param


def test_retrieve_known_formula(storage_implementation: StorageImplementation):
    storage: LogicObjectStorage = storage_implementation.storage_factory()

    IsA, dylan, cat = constants('IsA, dylan, cat')

    formula = IsA(dylan, cat)
    storage.add(formula)

    # we can retrieve it because we already know it
    all_retrieved = set(storage.search_unifiable(IsA(dylan, cat)))

    assert len(all_retrieved) == 1
    retrieved = all_retrieved.pop()
    assert retrieved == IsA(dylan, cat)

    if storage_implementation.preserves_identity:
        assert retrieved is formula
    else:
        assert retrieved is not formula


def test_retrieve_known_open_formula(storage_implementation: StorageImplementation):
    storage: LogicObjectStorage = storage_implementation.storage_factory()

    v = VariableSource()

    IsA, dylan, cat, hugo = constants('IsA, dylan, cat, hugo')

    storage.add(
        IsA(dylan, cat),
        IsA(hugo, cat)
    )

    retrieved = set(storage.search_unifiable(IsA(v._x, cat)))
    assert retrieved == {IsA(dylan, cat), IsA(hugo, cat)}


def test_normalized_formulas_added_only_once(storage_implementation: StorageImplementation):
    storage: LogicObjectStorage = storage_implementation.storage_factory()

    v = VariableSource()
    Foo, a, b = constants('Foo, a, b')

    normalizer = VariableSource()
    storage.add(*(
        normalize_variables(x, variable_source=normalizer)
        for x in (Foo(a, b), Foo(v.x, v.y), Foo(v.x, v.x), Foo(v.w, v.z))
    ))

    assert len(storage) == 3
