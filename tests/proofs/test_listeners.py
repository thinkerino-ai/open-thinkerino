from typing import List

import pytest

from aitools.logic import Substitution, Constant
from aitools.logic.utils import VariableSource, constants
from aitools.proofs.listeners import Listener, HandlerArgumentMode, HandlerSafety, PonderMode
from aitools.proofs.proof import Proof


def test_basic_listener(test_knowledge_base):
    v = VariableSource()

    Is, Meows, cat, dylan = constants('Is, Meows, cat, dylan')

    def cats_meow(cat):
        yield Meows(cat)

    listened_formula = Is(v.cat, cat)
    _listener = Listener(handler=cats_meow, listened_formula=listened_formula, argument_mode=HandlerArgumentMode.MAP,
                         pure=True, safety=HandlerSafety.SAFE)

    test_knowledge_base.add_listener(_listener)

    test_knowledge_base.add_formulas(Is(dylan, cat))

    proofs: List[Proof] = list(test_knowledge_base.ponder(Is(dylan, cat), ponder_mode=PonderMode.KNOWN))

    assert all(isinstance(p, Proof) for p in proofs)
    assert len(proofs) == 1

    proof: Proof = proofs.pop()

    assert proof.conclusion == Meows(dylan)
    assert set(p.conclusion for p in proof.premises) == {Is(dylan, cat)}


def test_listener_multiple_formulas_returned(test_knowledge_base):
    v = VariableSource()
    Is, Meows, Purrs, cat, dylan = constants('Is, Meows, Purrs, cat, dylan')

    @listener(Is(v._x, cat))
    def deduce_meow_and_purr(_x):
        return Meows(_x), Purrs(_x)

    test_knowledge_base.add_listener(deduce_meow_and_purr)
    test_knowledge_base.add_formulas(Is(dylan, cat))

    assert any(test_knowledge_base.prove(Meows(dylan)))
    assert any(test_knowledge_base.prove(Purrs(dylan)))


def test_listener_complex_conjunction(test_knowledge_base):
    v = VariableSource()
    IsParent, IsBrother, IsUncle, alice, bob, carl = constants('IsParent, IsBrother, IsUncle, alice, bob, carl')

    @listener(IsParent(v._a, v._b), IsBrother(v._c, v._a))
    def deduce_uncle(_b, _c):
        # note that since we don't care for _a we don't ask for it!
        return IsUncle(_c, _b)

    test_knowledge_base.add_listener(deduce_uncle)

    test_knowledge_base.add_formulas(IsBrother(carl, alice))

    assert not any(test_knowledge_base.prove(IsUncle(carl, bob)))

    test_knowledge_base.add_formulas(IsParent(alice, bob))

    assert any(test_knowledge_base.prove(IsUncle(carl, bob)))


def test_listener_complex_disjunction(test_knowledge_base):
    v = VariableSource()
    IsDog, IsBarkingHuman, Barks, luce, bard = constants('IsDog, IsBarkingHuman, Barks, luce, bard')

    @listener(IsDog(v._x))
    @listener(IsBarkingHuman(v._x))
    def deduce_barks(_x):
        # yeah it's a stupid example, but I'm on a train and I'm quite drunk :P
        # UPDATE: I'm on a plane now, not drunk, still stupid, still going with it :P
        return Barks(_x)

    test_knowledge_base.add_listener(deduce_barks)

    # if you ever heard The Fox: yep yep yep yep yep yepyep yepyep :P
    test_knowledge_base.add_formulas(IsDog(luce), IsBarkingHuman(bard))

    assert any(test_knowledge_base.prove(Barks(luce)))
    assert any(test_knowledge_base.prove(Barks(bard)))


def test_listener_manual_generation(test_knowledge_base):
    v = VariableSource()
    IsParent, IsBrother, IsUncle, alice, bob, carl = constants('IsParent, IsBrother, IsUncle, alice, bob, carl')

    @listener(v._formula)
    def deduce_uncle_but_in_a_weird_way(_formula):
        # this is one of the dumbest ways of doing it, but it shows what you can do with 'listen_for'
        subst = Substitution.unify(_formula, IsParent(v._a, v._b))
        if subst is not None:
            a = subst.get_bound_object_for(v._a)
            b = subst.get_bound_object_for(v._b)
            return Listener(lambda _c: IsUncle(_c, b), [IsBrother(v._c, a)], previous_substitution=subst)

        subst = Substitution.unify(_formula, IsBrother(v._c, v._a))
        if subst is not None:
            c = subst.get_bound_object_for(v._c)
            a = subst.get_bound_object_for(v._a)
            return Listener(lambda _b, _c: IsUncle(c, _b), [IsParent(a, v._b)], previous_substitution=subst)

    test_knowledge_base.add_listener(deduce_uncle_but_in_a_weird_way)
    test_knowledge_base.add_formulas(IsParent(alice, bob))

    test_knowledge_base.add_formulas(IsBrother(carl, alice))

    assert any(test_knowledge_base.prove(IsUncle(carl, bob)))

    test_knowledge_base.add_listener(deduce_uncle_but_in_a_weird_way)
    test_knowledge_base.add_formulas(IsBrother(carl, alice))

    test_knowledge_base.add_formulas(IsParent(alice, bob))
    assert any(test_knowledge_base.prove(IsUncle(carl, bob)))


def test_listener_chain(test_knowledge_base):
    v = VariableSource()
    A, B, C, D, foo = constants('A, B, C, D, foo')

    @listener(A(v._x))
    def deduce_from_a_b(_x):
        return B(_x)

    @listener(B(v._x))
    def deduce_from_b_c(_x):
        return C(_x)

    @listener(C(v._x))
    def deduce_from_c_d(_x):
        return D(_x)

    test_knowledge_base.add_listener(deduce_from_b_c)
    test_knowledge_base.add_listener(deduce_from_a_b)
    test_knowledge_base.add_listener(deduce_from_c_d)

    assert not any(test_knowledge_base.prove(D(foo)))

    test_knowledge_base.add_formulas(A(foo))

    assert any(test_knowledge_base.prove(D(foo)))


def test_listener_priority(test_knowledge_base):
    res = []

    Go = Constant(name='Go')

    @listener(Go(), priority=1)
    def listener_1():
        res.append(1)

    # default priority is 0
    @listener(Go())
    def listener_0():
        res.append(0)

    @listener(Go(), priority=2)
    def listener_2():
        res.append(2)

    test_knowledge_base.add_listener(listener_1)
    test_knowledge_base.add_listener(listener_0)
    test_knowledge_base.add_listener(listener_2)

    assert res == []

    test_knowledge_base.add_formulas(Go())

    assert res == [2, 1, 0]


@pytest.mark.xfail(reason="I'm too lazy to implement such a marginal thing")
def test_listener_consume(test_knowledge_base):
    def consume():
        pass

    Go = Constant(name='Go')

    consumer_triggered = False
    other_triggered = False

    @listener(Go, priority=1)
    def consumer():
        nonlocal consumer_triggered
        consumer_triggered = True
        consume()

    @listener(Go)
    def other():
        nonlocal other_triggered
        other_triggered = True
        consume()

    test_knowledge_base.add_listener(consumer, other)
    assert not consumer_triggered and not other_triggered

    test_knowledge_base.add_formulas(Go)
    assert consumer_triggered and not other_triggered