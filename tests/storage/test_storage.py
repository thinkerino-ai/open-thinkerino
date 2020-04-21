from dataclasses import dataclass
from typing import Callable

import pytest

from aitools.logic import Substitution
from aitools.logic.utils import constants, VariableSource, normalize_variables
from aitools.storage.base import LogicObjectStorage
from tests import implementations


@pytest.fixture(params=implementations.storage_implementations.values())
def storage_implementation(request):
    return request.param


def test_retrieve_known_formula(storage_implementation):
    storage: LogicObjectStorage = storage_implementation()

    IsA, dylan, cat = constants('IsA, dylan, cat')

    formula = IsA(dylan, cat)
    storage.add(formula)

    # we can retrieve it because we already know it
    all_retrieved = list(storage.search_unifiable(IsA(dylan, cat)))

    assert len(all_retrieved) == 1
    retrieved, unifier = all_retrieved.pop()

    assert isinstance(unifier, Substitution)
    assert retrieved == IsA(dylan, cat)


def test_retrieve_known_open_formula(storage_implementation):
    storage: LogicObjectStorage = storage_implementation()

    v = VariableSource()

    IsA, dylan, cat, hugo = constants('IsA, dylan, cat, hugo')

    storage.add(
        IsA(dylan, cat),
        IsA(hugo, cat)
    )

    retrieved = set(formula for formula, unifier in storage.search_unifiable(IsA(v._x, cat)))
    assert retrieved == {IsA(dylan, cat), IsA(hugo, cat)}


def test_normalized_formulas_added_only_once(storage_implementation):
    storage: LogicObjectStorage = storage_implementation()

    v = VariableSource()
    Foo, a, b = constants('Foo, a, b')

    normalizer = VariableSource()
    storage.add(*(
        normalize_variables(x, variable_source=normalizer)
        for x in (Foo(a, b), Foo(v.x, v.y), Foo(v.x, v.x), Foo(v.w, v.z))
    ))

    assert len(storage) == 3
