import pytest

from aitools.logic.core import Expression
from aitools.logic.utils import constants, wrap, VariableSource
from aitools.proofs.builtin_provers import RestrictedModusPonens, ClosedWorldAssumption
from aitools.proofs.components import HandlerSafety, HandlerArgumentMode
from aitools.proofs.knowledge_base import KnowledgeBase
from aitools.proofs.language import Implies, MagicPredicate, Not
from aitools.proofs.provers import Proof, Prover, TruthSubstitutionPremises


def test_retrieve_known_formula(test_knowledge_base):
    # TODO this now is more or less duplicated in test_storage, I need to decide what to do with it

    IsA, dylan, cat = constants('IsA, dylan, cat')
    test_knowledge_base.add_formulas(IsA(dylan, cat))
    # we can retrieve it because we already know it
    proofs = list(test_knowledge_base.prove(IsA(dylan, cat), retrieve_only=True))

    assert len(proofs) == 1
    assert all(isinstance(p, Proof) for p in proofs)
    assert all(proof.conclusion == IsA(dylan, cat) for proof in proofs)


def test_retrieve_known_formula_transactional(test_knowledge_base):
    if not test_knowledge_base.supports_transactions():
        pytest.skip("KB implementation doesn't support transactions")

    IsA, dylan, cat = constants('IsA, dylan, cat')

    with test_knowledge_base.transaction():
        test_knowledge_base.add_formulas(IsA(dylan, cat))

    substitutions = list(test_knowledge_base.prove(IsA(dylan, cat), retrieve_only=True))

    assert len(substitutions) == 1


def test_retrieve_known_formula_rollback(test_knowledge_base):
    if not test_knowledge_base.supports_transactions():
        pytest.skip("KB implementation doesn't support transactions")

    class VeryCustomException(Exception):
        pass

    IsA, dylan, cat = constants('IsA, dylan, cat')

    with pytest.raises(VeryCustomException):
        with test_knowledge_base.transaction():
            test_knowledge_base.add_formulas(IsA(dylan, cat))
            raise VeryCustomException()

    substitutions = list(test_knowledge_base.prove(IsA(dylan, cat), retrieve_only=True))
    assert len(substitutions) == 0


def test_retrieve_known_open_formula(test_knowledge_base):
    # TODO this now is more or less duplicated in test_storage, I need to decide what to do with it
    v = VariableSource()

    IsA, dylan, cat, hugo = constants('IsA, dylan, cat, hugo')

    test_knowledge_base.add_formulas(
        IsA(dylan, cat),
        IsA(hugo, cat)
    )

    proofs = list(test_knowledge_base.prove(IsA(v._x, cat), retrieve_only=True))
    assert len(proofs) == 2

    assert all(isinstance(p, Proof) for p in proofs)

    assert any(proof.substitution.apply_to(proof.conclusion) == IsA(dylan, cat) for proof in proofs)
    assert any(proof.substitution.apply_to(proof.conclusion) == IsA(hugo, cat) for proof in proofs)


def test_open_formulas_added_only_once(test_knowledge_base):
    # TODO this now is more or less duplicated in test_storage, I need to decide what to do with it
    v = VariableSource()

    Foo, a, b = constants('Foo, a, b')

    test_knowledge_base.add_formulas(Foo(a, b), Foo(v.x, v.y), Foo(v.x, v.x), Foo(v.w, v.z))

    assert len(test_knowledge_base) == 3


def test_formulas_are_be_normalized(test_knowledge_base):
    v = VariableSource()

    Foo, Bar, Baz, a, b = constants('Foo, Bar, Baz, a, b')

    test_knowledge_base.add_prover(RestrictedModusPonens)

    test_knowledge_base.add_formulas(
        Foo(a, b),
        Foo(v.x, v.y) << Implies >> Bar(v.x),
        Bar(v.y) << Implies >> Baz(v.y)
    )

    proofs = list(test_knowledge_base.prove(Baz(a)))
    assert any(proofs)


def test_open_formulas_can_be_used_more_than_once(test_knowledge_base):
    v = VariableSource()

    IsNatural, successor = constants('IsNatural, successor')

    test_knowledge_base.add_prover(RestrictedModusPonens)

    test_knowledge_base.add_formulas(
        IsNatural(wrap(0)),
        IsNatural(v.x) << Implies >> IsNatural(successor(v.x))
    )

    baseline_proofs = list(test_knowledge_base.prove(IsNatural(successor(wrap(0)))))
    assert any(baseline_proofs)

    # actual test
    proofs = list(test_knowledge_base.prove(IsNatural(successor(successor(wrap(0))))))
    assert any(proofs)


def _is_known_formula_proof_of(proof: Proof, formula: Expression, kb: KnowledgeBase) -> bool:
    return (isinstance(proof, Proof) and not any(proof.premises) and
            proof.inference_rule is kb.knowledge_retriever and
            proof.substitution.apply_to(formula) == proof.substitution.apply_to(proof.conclusion))


def test_proof_known_formula(test_knowledge_base):
    IsA, dylan, cat = constants('IsA, dylan, cat')

    test_knowledge_base.add_formulas(IsA(dylan, cat))

    target = IsA(dylan, cat)
    proofs = list(test_knowledge_base.prove(target))

    # at least one way to prove it directly!
    assert all(_is_known_formula_proof_of(p, target, kb=test_knowledge_base) for p in proofs)
    assert any(proofs)


def test_proof_known_open_formula(test_knowledge_base):
    v = VariableSource()

    IsA, dylan, hugo, cat = constants('IsA, dylan, hugo, cat')

    test_knowledge_base.add_formulas(
        IsA(dylan, cat),
        IsA(hugo, cat)
    )

    target = IsA(v._x, cat)
    proofs = list(test_knowledge_base.prove(target))
    assert len(proofs) == 2
    assert all(_is_known_formula_proof_of(proof, target, kb=test_knowledge_base) for proof in proofs)

    assert any(p.substitution.get_bound_object_for(v._x) == dylan for p in proofs)
    assert any(p.substitution.get_bound_object_for(v._x) == hugo for p in proofs)


def test_implication_shortcut():
    v = VariableSource()
    IsA, cat, animal = constants('IsA, cat, animal')
    assert (IsA(v._x, cat) << Implies >> IsA(v._x, animal)) == (Implies(IsA(v._x, cat), IsA(v._x, animal)))


def test_simple_deduction(test_knowledge_base):
    v = VariableSource()

    IsA, cat, animal, dylan = constants('IsA, cat, animal, dylan')

    test_knowledge_base.add_prover(RestrictedModusPonens)

    test_knowledge_base.add_formulas(
        IsA(v._x, cat) << Implies >> IsA(v._x, animal)
    )

    test_knowledge_base.add_formulas(IsA(dylan, cat))

    proofs = list(test_knowledge_base.prove(IsA(dylan, animal)))
    assert any(proofs)
    assert all(isinstance(p, Proof) for p in proofs)


def test_retrieve_known_formula_does_not_use_deduction(test_knowledge_base):
    # this is the same as the basic retrieve case, but ensures deduction is not used

    v = VariableSource()

    IsA, Purrs, dylan, cat = constants('IsA, Purrs, dylan, cat')
    test_knowledge_base.add_formulas(
        IsA(dylan, cat),
        Purrs(dylan)
    )

    # if it purrs like a cat, then it's a cat :P
    test_knowledge_base.add_formulas(
        Purrs(v.x) <<Implies>> IsA(v.x, cat)
    )

    # we can retrieve it because we already know it
    proofs = list(test_knowledge_base.prove(IsA(dylan, cat), retrieve_only=True))

    assert len(proofs) == 1


def test_deduction_chain(test_knowledge_base):
    v = VariableSource()

    IsA, cat, mammal, animal, dylan = constants('IsA, cat, mammal, animal, dylan')

    test_knowledge_base.add_prover(RestrictedModusPonens)

    test_knowledge_base.add_formulas(
        IsA(v._x, cat) << Implies >> IsA(v._x, mammal),
        IsA(v._x, mammal) << Implies >> IsA(v._x, animal),
        IsA(dylan, cat)
    )

    proofs = list(test_knowledge_base.prove(IsA(dylan, animal)))

    assert any(proofs)

    assert len(proofs[0].premises) > 0


def is_even(n: int):
    if n % 2 == 0:
        return True
    else:
        return False


IsEven = MagicPredicate('IsEven')
IsMultipleOf4 = MagicPredicate('IsMultipleOf4')


def test_simple_custom_prover_passing_python_value(test_knowledge_base):
    v = VariableSource()

    prover = Prover(
        listened_formula=IsEven(v.n), handler=is_even, argument_mode=HandlerArgumentMode.MAP_UNWRAPPED_REQUIRED,
        pass_substitution_as=..., pure=True, safety=HandlerSafety.SAFE
    )

    test_knowledge_base.add_prover(prover)

    assert any(test_knowledge_base.prove(IsEven(2)))

    # this means we can't prove it, not that we can prove it is false
    assert not any(test_knowledge_base.prove(IsEven(3)))


def test_failing_custom_prover(test_knowledge_base):
    class SomeException(Exception):
        pass

    v = VariableSource()

    Is, cat, dylan = constants('Is, cat, dylan')

    def failing_prover(cat):
        raise SomeException(f"Oh noes I failed with {cat}")

    listened_formula = Is(v.cat, cat)
    failing = Prover(listened_formula=listened_formula, handler=failing_prover, argument_mode=HandlerArgumentMode.MAP,
                     pass_substitution_as=..., pure=True, safety=HandlerSafety.TOTALLY_UNSAFE)

    test_knowledge_base.add_prover(failing)

    test_knowledge_base.add_formulas(Is(dylan, cat))

    with pytest.raises(SomeException):
        try:
            list(test_knowledge_base.prove(Is(dylan, cat)))
        except Exception as e:
            raise e


async def is_multiple_of_4(m: int, kb):
    async for proof in kb.async_prove(IsEven(m // 2)):
        yield TruthSubstitutionPremises(True, proof.substitution, proof)


def test_custom_prover_chain(test_knowledge_base):
    v = VariableSource()

    even_prover = Prover(
        listened_formula=IsEven(v.n), handler=is_even, argument_mode=HandlerArgumentMode.MAP_UNWRAPPED_REQUIRED,
        pass_substitution_as=..., pure=True, safety=HandlerSafety.SAFE
    )
    multiple_of_4_prover = Prover(
        listened_formula=IsMultipleOf4(v.m), handler=is_multiple_of_4,
        argument_mode=HandlerArgumentMode.MAP_UNWRAPPED_REQUIRED, pass_substitution_as=...,
        pass_knowledge_base_as='kb', pure=True,
        safety=HandlerSafety.SAFE
    )

    test_knowledge_base.add_prover(even_prover)
    test_knowledge_base.add_prover(multiple_of_4_prover)

    proofs = list(test_knowledge_base.prove(IsMultipleOf4(20)))
    assert len(proofs[0].premises) > 0


def test_custom_prover_in_open_formula(test_knowledge_base):
    v = VariableSource()

    IsNice = MagicPredicate()

    prover = Prover(
        listened_formula=IsEven(v.n), handler=is_even, argument_mode=HandlerArgumentMode.MAP_UNWRAPPED_REQUIRED,
        pass_substitution_as=..., pure=True, safety=HandlerSafety.SAFE
    )

    test_knowledge_base.add_prover(prover)
    test_knowledge_base.add_prover(RestrictedModusPonens)

    # I don't actually like even numbers, unless they are powers of 2
    test_knowledge_base.add_formulas(IsEven(v._x) << Implies >> IsNice(v._x))

    assert any(test_knowledge_base.prove(IsNice(32)))


def is_prime(n: int):
    if n in (2, 3, 5, 7):
        return True
    if n in (4, 6, 8):
        return False
    # None means "Who knows?"
    return None


def test_custom_prover_incomplete(test_knowledge_base):
    v = VariableSource()

    IsPrime = MagicPredicate()

    prover = Prover(
        listened_formula=IsPrime(v.n), handler=is_prime, argument_mode=HandlerArgumentMode.MAP_UNWRAPPED_REQUIRED,
        pass_substitution_as=..., pure=True, safety=HandlerSafety.SAFE
    )

    test_knowledge_base.add_prover(prover)
    test_knowledge_base.add_prover(RestrictedModusPonens)

    assert any(test_knowledge_base.prove(IsPrime(2)))
    assert not any(test_knowledge_base.prove(IsPrime(10)))


def test_multiple_custom_provers_for_the_same_formula(test_knowledge_base):
    v = VariableSource()
    IsPrime = MagicPredicate()

    def prime_prover_012345(n: int):
        if n in (2, 3, 5):
            return True
        if n in (0, 1, 4):
            return False
        return None

    def prime_prover_456789(n: int):
        if n in (5, 7):
            return True
        if n in (4, 6, 8, 9):
            return False
        return None

    prover1 = Prover(
        listened_formula=IsPrime(v.n), handler=prime_prover_012345,
        argument_mode=HandlerArgumentMode.MAP_UNWRAPPED_REQUIRED, pass_substitution_as=..., pure=True,
        safety=HandlerSafety.SAFE
    )

    prover2 = Prover(
        listened_formula=IsPrime(v.n), handler=prime_prover_456789,
        argument_mode=HandlerArgumentMode.MAP_UNWRAPPED_REQUIRED, pass_substitution_as=..., pure=True,
        safety=HandlerSafety.SAFE
    )

    test_knowledge_base.add_prover(prover1)
    test_knowledge_base.add_prover(prover2)

    assert any(test_knowledge_base.prove(IsPrime(2)))
    assert any(test_knowledge_base.prove(IsPrime(7)))

    assert len(list(test_knowledge_base.prove(IsPrime(5)))) == 2

    assert not any(test_knowledge_base.prove(IsPrime(11)))


def test_closed_world_assumption(test_knowledge_base):
    v = VariableSource()

    IsPrime = MagicPredicate()

    prover = Prover(
        listened_formula=IsPrime(v.n), handler=is_prime, argument_mode=HandlerArgumentMode.MAP_UNWRAPPED_REQUIRED,
        pass_substitution_as=..., pure=True, safety=HandlerSafety.SAFE
    )

    test_knowledge_base.add_prover(prover)
    test_knowledge_base.add_prover(RestrictedModusPonens)

    assert not any(test_knowledge_base.prove(Not(IsPrime(4))))

    test_knowledge_base.add_prover(ClosedWorldAssumption)

    assert any(test_knowledge_base.prove(Not(IsPrime(4))))


@pytest.mark.xfail(reason="me == lazy")
def test_result_order():
    # TODO this test should use "complex" chains and show that results are generated breadth-first-ish
    raise NotImplementedError()


@pytest.mark.xfail(reason="me == lazy")
def test_handler_result_types():
    # TODO this should actually be several tests that check every possible type returned by a handler (sync and async)
    raise NotImplementedError()


@pytest.mark.xfail(reason="Come on, we can bring coverage up :P")
def test_many_more_cases():
    raise NotImplementedError("Implement all possible input modes")