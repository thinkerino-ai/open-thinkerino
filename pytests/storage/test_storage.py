import pytest

from aitools.logic.language import Language
from aitools.logic.unification import Substitution
from aitools.logic.utils import constants, VariableSource, normalize_variables
from aitools.storage.base import LogicObjectStorage
from tests import implementations


@pytest.fixture(params=implementations.storage_implementations)
def test_storage(request) -> LogicObjectStorage:
    with request.param() as storage:
        yield storage


def test_retrieve_known_formula(test_storage):
    language = Language()
    IsA, dylan, cat = constants('IsA, dylan, cat', language=language)

    formula = IsA(dylan, cat)
    test_storage.add(formula)

    # we can retrieve it because we already know it
    all_retrieved = list(test_storage.search_unifiable(IsA(dylan, cat)))

    assert len(all_retrieved) == 1
    retrieved, unifier = all_retrieved.pop()

    assert isinstance(unifier, Substitution)
    assert retrieved == IsA(dylan, cat)


def test_retrieve_known_open_formula(test_storage):
    language = Language()
    v = VariableSource(language=language)

    IsA, dylan, cat, hugo = constants('IsA, dylan, cat, hugo', language=language)

    test_storage.add(
        IsA(dylan, cat),
        IsA(hugo, cat)
    )

    retrieved = set(formula for formula, unifier in test_storage.search_unifiable(IsA(v._x, cat)))
    assert retrieved == {IsA(dylan, cat), IsA(hugo, cat)}


def test_normalized_formulas_added_only_once(test_storage):
    language = Language()
    v = VariableSource(language=language)
    Foo, a, b = constants('Foo, a, b', language=language)

    normalizer = VariableSource(language=language)
    normalized_formulas = (
        normalize_variables(x, variable_source=normalizer)
        for x in (Foo(a, b), Foo(v.x, v.y), Foo(v.x, v.x), Foo(v.w, v.z))
    )
    test_storage.add(*(formula for formula, mapping in normalized_formulas))

    assert len(test_storage) == 3


def test_retrieve_known_formula_transactional(test_storage):
    if not test_storage.supports_transactions():
        pytest.skip("Storage doesn't support transactions")

    language = Language()

    IsA, dylan, cat = constants('IsA, dylan, cat', language=language)
    formula = IsA(dylan, cat)

    with test_storage.transaction():
        test_storage.add(formula)

    # we can retrieve it because we already know it
    all_retrieved = list(test_storage.search_unifiable(IsA(dylan, cat)))

    assert len(all_retrieved) == 1
    retrieved, unifier = all_retrieved.pop()

    assert isinstance(unifier, Substitution)
    assert retrieved == IsA(dylan, cat)


def test_retrieve_known_formula_rollback(test_storage):
    if not test_storage.supports_transactions():
        pytest.skip("Storage doesn't support transactions")
    language = Language()
    IsA, dylan, cat = constants('IsA, dylan, cat', language=language)
    formula = IsA(dylan, cat)

    class VeryCustomException(Exception):
        pass

    with pytest.raises(VeryCustomException):
        with test_storage.transaction():
            test_storage.add(formula)
            raise VeryCustomException()

    # we can retrieve it because we already know it
    all_retrieved = list(test_storage.search_unifiable(IsA(dylan, cat)))

    assert len(all_retrieved) == 0
