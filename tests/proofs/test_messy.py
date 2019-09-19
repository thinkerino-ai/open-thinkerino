import pytest

from aitools.logic import Variable, Constant, Substitution, Expression
from aitools.logic.utils import subst, constants, wrap, VariableSource
from aitools.proofs.knowledge_bases.dummy import DummyKnowledgeBase
from aitools.proofs.language import Implies, MagicPredicate, Not
from aitools.proofs.listeners import listener, Listener
from aitools.proofs.proof import Proof
from aitools.proofs.provers import KnowledgeRetriever, NegationProver
from aitools.proofs.utils import predicate_function


def test_retrieve_known_formula():
    kb = DummyKnowledgeBase()

    IsA, dylan, cat = constants('IsA, dylan, cat')

    kb.add_formulas(IsA(dylan, cat))

    # we can retrieve it because we already know it
    substitutions = list(kb.retrieve(IsA(dylan, cat)))

    assert any(substitutions)
    assert all(isinstance(s, Substitution) for s in substitutions)


def test_retrieve_known_open_formula():
    v = VariableSource()
    kb = DummyKnowledgeBase()

    IsA, dylan, cat, hugo = constants('IsA, dylan, cat, hugo')

    kb.add_formulas(
        IsA(dylan, cat),
        IsA(hugo, cat)
    )

    substitutions = list(kb.retrieve(IsA(v._x, cat)))
    assert len(substitutions) == 2

    assert all(isinstance(s, Substitution) for s in substitutions)

    assert any(substitution.get_bound_object_for(v._x) == dylan for substitution in substitutions)
    assert any(substitution.get_bound_object_for(v._x) == hugo for substitution in substitutions)


def test_open_formulas_added_only_once():
    v = VariableSource()
    kb = DummyKnowledgeBase()
    Foo, a, b = constants('Foo, a, b')

    kb.add_formulas(Foo(a, b), Foo(v.x, v.y), Foo(v.x, v.x), Foo(v.w, v.z))

    assert len(kb._known_formulas) == 3


def test_formulas_must_be_normalized():
    v = VariableSource()
    kb = DummyKnowledgeBase()
    Foo, Bar, Baz, a, b = constants('Foo, Bar, Baz, a, b')

    kb.add_formulas(
        Foo(a, b),
        Foo(v.x, v.y) <<Implies>> Bar(v.x),
        Bar(v.y) <<Implies>> Baz(v.y)
    )

    #ERROR continuare da qui, non funziona perché la retrieve deve sempre normalizzare le variabili prima
    #NOTA CHE HO AGGIUNTO GIA' LA RENEW ALLA add_formulas
    proofs = list(kb.prove(Baz(a)))
    assert any(proofs)
    print(repr(proofs))


def _is_known_formula_proof_of(proof: Proof, formula: Expression) -> bool:
    return (isinstance(proof, Proof) and not any(proof.premises) and
            isinstance(proof.inference_rule, KnowledgeRetriever) and
            proof.substitution.apply_to(formula) == proof.substitution.apply_to(proof.conclusion))


def test_proof_known_formula():

    kb = DummyKnowledgeBase()

    IsA, dylan, cat = constants('IsA, dylan, cat')

    kb.add_formulas(IsA(dylan, cat))

    target = IsA(dylan, cat)
    proofs = list(kb.prove(target))

    # at least one way to prove it directly!
    assert all(_is_known_formula_proof_of(p, target) for p in proofs)
    assert any(proofs)


def test_proof_known_open_formula():
    v = VariableSource()
    kb = DummyKnowledgeBase()

    IsA, dylan, hugo, cat = constants('IsA, dylan, hugo, cat')

    kb.add_formulas(
        IsA(dylan, cat),
        IsA(hugo, cat)
    )

    target = IsA(v._x, cat)
    proofs = list(kb.prove(target))
    assert len(proofs) == 2
    assert all(_is_known_formula_proof_of(proof, target) for proof in proofs)

    assert any(p.substitution.get_bound_object_for(v._x) == dylan for p in proofs)
    assert any(p.substitution.get_bound_object_for(v._x) == hugo for p in proofs)


def test_implication_shortcut():
    v = VariableSource()
    IsA, cat, animal = constants('IsA, cat, animal')
    assert (IsA(v._x, cat) <<Implies>> IsA(v._x, animal)) == (Implies(IsA(v._x, cat), IsA(v._x, animal)))


def test_simple_deduction():
    v = VariableSource()
    kb = DummyKnowledgeBase()

    IsA, cat, animal, dylan = constants('IsA, cat, animal, dylan')

    kb.add_formulas(
        IsA(v._x, cat) <<Implies>> IsA(v._x, animal)
    )

    kb.add_formulas(IsA(dylan, cat))

    proofs = list(kb.prove(IsA(dylan, animal)))
    assert any(proofs)
    assert all(isinstance(p, Proof) for p in proofs)


def test_deduction_chain():
    v = VariableSource()
    kb = DummyKnowledgeBase()

    IsA, cat, mammal, animal, dylan = constants('IsA, cat, mammal, animal, dylan')

    kb.add_formulas(
        IsA(v._x, cat) <<Implies>> IsA(v._x, mammal),
        IsA(v._x, mammal) <<Implies>> IsA(v._x, animal),
        IsA(dylan, mammal)
    )

    proofs = list(kb.prove(IsA(dylan, animal)))

    assert any(proofs)

    assert len(proofs[0].premises) > 0

@predicate_function
def IsEven(n: int):
    if n % 2 == 0:
        return True
    else:
        return False


def test_simple_custom_prover_passing_python_value():
    kb = DummyKnowledgeBase()

    assert any(kb.prove(IsEven(2)))

    # this means we can't prove it, not that we can prove it is false
    assert not any(kb.prove(IsEven(3)))


def test_simple_custom_prover_to_be_false():
    kb = DummyKnowledgeBase()

    # now *this* means that we can prove it is false :P
    assert any(kb.prove(IsEven(3), truth=False))


@predicate_function
def IsMultipleOf4(n: int):
    from aitools.proofs.context import prove
    if prove(IsEven(n // 2)):
        return True
    elif prove(IsEven(n // 2), truth=False):
        return False


@pytest.mark.xfail(reason="This needs to be implemented, but it's too complex for my little sleepy brain right now :P")
def test_custom_prover_chain_adds_premises():
    kb = DummyKnowledgeBase()

    proofs = list(kb.prove(IsMultipleOf4(20)))
    assert len(proofs[0].premises) > 0


def test_custom_prover_chain():
    kb = DummyKnowledgeBase()

    proofs = list(kb.prove(IsMultipleOf4(20)))
    assert any(proofs)

    # this means we can't prove it, not that we can prove it is false
    assert not any(kb.prove(IsMultipleOf4(14)))


def test_custom_prover_in_open_formula():
    v = VariableSource()
    kb = DummyKnowledgeBase()

    IsNice = MagicPredicate()

    # I don't actually like even numbers, unless they are powers of 2
    kb.add_formulas(IsEven(v._x) <<Implies>> IsNice(v._x))

    # ok maybe this IS necessary :P otherwise the kb doesn't know how to use it
    kb.add_provers(IsEven)

    assert any(kb.prove(IsNice(32)))


def test_custom_prover_with_explicit_formula():
    v = VariableSource()
    kb = DummyKnowledgeBase()

    IsPayload = MagicPredicate()

    @predicate_function(proves=IsPayload(v._x))
    def name_here_does_not_matter(x: dict):
        return isinstance(x, dict) and isinstance(x['code'], int) and isinstance(x['message'], str)

    kb.add_provers(name_here_does_not_matter)

    assert any(kb.prove(
        IsPayload({'code': 200, 'message': 'success!'})
    ))


def test_custom_prover_incomplete():
    # this prover can only prove its formula in some cases
    @predicate_function
    def IsPrime(n: int):
        if n in (2, 3, 5, 7):
            return True
        if n in (4, 6, 8):
            return False
        # None means "Who knows?"
        return None

    kb = DummyKnowledgeBase()

    kb.add_provers(NegationProver())

    assert any(kb.prove(IsPrime(2)))
    assert any(kb.prove(Not(IsPrime(4))))
    assert not any(kb.prove(IsPrime(10)))
    assert not any(kb.prove(Not(IsPrime(10))))


def test_multiple_custom_provers_for_the_same_formula():
    v = VariableSource()
    IsPrime = MagicPredicate()

    @predicate_function(proves=IsPrime(v._n))
    def prime_prover_012345(_n: int):
        if _n in (2, 3, 5):
            return True
        if _n in (0, 1, 4):
            return False
        return None

    @predicate_function(proves=IsPrime(v._n))
    def prime_prover_456789(_n: int):
        if _n in (5, 7):
            return True
        if _n in (4, 6, 8, 9):
            return False
        return None

    kb = DummyKnowledgeBase()

    kb.add_provers(prime_prover_012345, prime_prover_456789, NegationProver())

    assert any(kb.prove(IsPrime(2)))
    assert any(kb.prove(IsPrime(7)))
    assert any(kb.prove(Not(IsPrime(0))))
    assert any(kb.prove(Not(IsPrime(8))))

    assert len(list(kb.prove(IsPrime(5)))) == 2
    assert len(list(kb.prove(Not(IsPrime(4))))) == 2

    assert not any(kb.prove(IsPrime(11)))
    assert not any(kb.prove(Not(IsPrime(11))))


def test_prover_returning_substitutions():
    v = VariableSource()
    @predicate_function
    def Likes(_x: str, _y: str):
        """We prove that lisa likes nelson and milhouse likes lisa.
        We also prove that nobody likes milhouse."""
        like_pairs = [("lisa", "nelson"), ("milhouse", "lisa")]
        if (_x, _y) in like_pairs:
            return True
        if _y == "milhouse":
            # you know where I'm going with this :P
            return False

        # this is ugly, I know, but I slept very little and this is a synthetic example off the top of my head :P
        if isinstance(_x, Variable) and isinstance(_y, Variable):
            return None

        if isinstance(_x, Variable):
            var = _x
            val = _y
            map = {likee: liker for liker, likee in like_pairs}
        elif isinstance(_y, Variable):
            var = _y
            val = _x
            map = dict(like_pairs)
        else:
            return None

        if val not in map:
            return None
        else:
            return True, subst((wrap(map[val]), [var]))

    kb = DummyKnowledgeBase()

    assert (kb.prove(Likes("lisa", "nelson")))

    lisa_likes_proofs = list(kb.prove(Likes("lisa", v._y)))
    assert (len(lisa_likes_proofs) == 1)
    assert (any(p.substitution.get_bound_object_for(v._y) == 'nelson' for p in lisa_likes_proofs))

    likes_lisa_proofs = list(kb.prove(Likes(v._y, "lisa")))
    assert (len(likes_lisa_proofs) == 1)
    assert (any(p.substitution.get_bound_object_for(v._y) == "milhouse") for p in lisa_likes_proofs)

    # nobody likes milhouse
    assert (not any(kb.prove(Likes(v._y, "milhouse"))))


def test_prover_returning_substitution_false():
    v = VariableSource()
    @predicate_function
    def Likes(_x, _y):
        if _x == "lisa" and isinstance(_y, Variable):
            return False, subst((wrap("milhouse"), [_y]))

        return None

    kb = DummyKnowledgeBase()

    kb.add_provers(NegationProver())

    assert not any(kb.prove(Likes("lisa", "milhouse")))

    assert any(kb.prove(Not(Likes("lisa", v._y))))


def test_prover_returning_multiple_results():
    v = VariableSource()
    @predicate_function
    def In(_x, _collection):

        if isinstance(_x, Variable):
            for el in _collection:
                yield subst((wrap(el), [_x]))
        else:
            yield _x in _collection

    kb = DummyKnowledgeBase()

    kb.add_provers(NegationProver())

    assert any(kb.prove(In(3, [1, 2, 3])))
    assert any(kb.prove(Not(In(4, [1, 2, 3]))))

    assert not any(kb.prove(In(4, [1, 2, 3])))
    assert not any(kb.prove(Not(In(3, [1, 2, 3]))))

    assert len(list(kb.prove(In(v._x, [1, 2, 3])))) == 3


@pytest.mark.xfail(reason="I'm not even sure if it should be done :P")
def test_listener_simple_retroactive():
    v = VariableSource()
    Is, Meows, cat, dylan = constants('Is, Meows, cat, dylan')
    triggered = False

    @listener(Is(v._x, cat))
    def deduce_meow(_x):
        nonlocal triggered
        triggered = True
        return Meows(_x)

    kb = DummyKnowledgeBase()

    kb.add_formulas(Is(dylan, cat))

    assert not any(kb.prove(Meows(dylan)))

    kb.add_listeners(deduce_meow, retroactive=True)

    assert triggered, "The listener should have triggered retroactively!"

    assert any(kb.prove(Meows(dylan)))


def test_listener_simple_non_retroactive():
    v = VariableSource()
    triggered = False
    Is, Meows, cat, dylan = constants('Is, Meows, cat, dylan')

    @listener(Is(v._x, cat))
    def deduce_meow(_x):
        nonlocal triggered
        triggered = True
        return Meows(_x)

    kb = DummyKnowledgeBase()

    kb.add_formulas(Is(dylan, cat))

    kb.add_listeners(deduce_meow, retroactive=False)

    assert not triggered, "The listener should **not** have triggered retroactively!"

    assert not any(kb.prove(Meows(dylan)))

    _ = next(iter(kb.prove(Is(dylan, cat))))

    assert triggered, "The listener should have triggered!"

    assert any(kb.prove(Meows(dylan)))


def test_listener_multiple_formulas_returned():
    v = VariableSource()
    Is, Meows, Purrs, cat, dylan = constants('Is, Meows, Purrs, cat, dylan')

    @listener(Is(v._x, cat))
    def deduce_meow_and_purr(_x):
        return Meows(_x), Purrs(_x)

    kb = DummyKnowledgeBase()

    kb.add_listeners(deduce_meow_and_purr)
    kb.add_formulas(Is(dylan, cat))

    assert any(kb.prove(Meows(dylan)))
    assert any(kb.prove(Purrs(dylan)))


def test_listener_complex_conjunction():
    v = VariableSource()
    IsParent, IsBrother, IsUncle, alice, bob, carl = constants('IsParent, IsBrother, IsUncle, alice, bob, carl')

    @listener(IsParent(v._a, v._b), IsBrother(v._c, v._a))
    def deduce_uncle(_b, _c):
        # note that since we don't care for _a we don't ask for it!
        return IsUncle(_c, _b)

    kb = DummyKnowledgeBase()

    kb.add_listeners(deduce_uncle)

    kb.add_formulas(IsBrother(carl, alice))

    assert not any(kb.prove(IsUncle(carl, bob)))

    kb.add_formulas(IsParent(alice, bob))

    assert any(kb.prove(IsUncle(carl, bob)))


def test_listener_complex_disjunction():
    v = VariableSource()
    IsDog, IsBarkingHuman, Barks, luce, bard = constants('IsDog, IsBarkingHuman, Barks, luce, bard')

    @listener(IsDog(v._x))
    @listener(IsBarkingHuman(v._x))
    def deduce_barks(_x):
        # yeah it's a stupid example, but I'm on a train and I'm quite drunk :P
        # UPDATE: I'm on a plane now, not drunk, still stupid, still going with it :P
        return Barks(_x)

    kb = DummyKnowledgeBase()

    kb.add_listeners(deduce_barks)

    # if you ever heard The Fox: yep yep yep yep yep yepyep yepyep :P
    kb.add_formulas(IsDog(luce), IsBarkingHuman(bard))

    assert any(kb.prove(Barks(luce)))
    assert any(kb.prove(Barks(bard)))


def test_listener_manual_generation():
    v = VariableSource()
    IsParent, IsBrother, IsUncle, alice, bob, carl = constants('IsParent, IsBrother, IsUncle, alice, bob, carl')

    @listener(v._formula)
    def deduce_uncle_but_in_a_weird_way(_formula):
        # this is one of the dumbest ways of doing it, but it shows what you can do with 'listen_for'
        subst = Substitution.unify(_formula, IsParent(v._a, v._b))
        if subst is not None:
            a = subst.get_bound_object_for(v._a)
            b = subst.get_bound_object_for(v._b)
            return Listener(lambda _c: IsUncle(_c, b), IsBrother(v._c, a), previous_substitution=subst)

        subst = Substitution.unify(_formula, IsBrother(v._c, v._a))
        if subst is not None:
            c = subst.get_bound_object_for(v._c)
            a = subst.get_bound_object_for(v._a)
            return Listener(lambda _b, _c: IsUncle(c, _b), IsParent(a, v._b), previous_substitution=subst)

    kb = DummyKnowledgeBase()

    kb.add_listeners(deduce_uncle_but_in_a_weird_way)
    kb.add_formulas(IsParent(alice, bob))

    kb.add_formulas(IsBrother(carl, alice))

    assert any(kb.prove(IsUncle(carl, bob)))

    kb = DummyKnowledgeBase()

    kb.add_listeners(deduce_uncle_but_in_a_weird_way)
    kb.add_formulas(IsBrother(carl, alice))

    kb.add_formulas(IsParent(alice, bob))
    assert any(kb.prove(IsUncle(carl, bob)))


def test_listener_chain():
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

    kb = DummyKnowledgeBase()

    kb.add_listeners(deduce_from_b_c)
    kb.add_listeners(deduce_from_a_b)
    kb.add_listeners(deduce_from_c_d)

    assert not any(kb.prove(D(foo)))

    kb.add_formulas(A(foo))

    assert any(kb.prove(D(foo)))


def test_listener_priority():
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

    kb = DummyKnowledgeBase()
    kb.add_listeners(listener_1, listener_0, listener_2)

    assert res == []

    kb.add_formulas(Go())

    assert res == [2, 1, 0]


@pytest.mark.xfail(reason="I'm too lazy to implement such a marginal thing")
def test_listener_consume():
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

    kb = DummyKnowledgeBase()
    kb.add_listeners(consumer, other)
    assert not consumer_triggered and not other_triggered

    kb.add_formulas(Go)
    assert consumer_triggered and not other_triggered


# altri casi:
# - evaluator (come il prover, ma restituisce un valore/oggetto anziché True/False/Substitution, oppure solleva eccezione se l'oggetto non è ancora abbastanza bound)
# - evaluator generato da un prover (simboli funzionali)
# - prover da un evaluator?
# - 0-step proof -> cose che so già senza dover ragionare
#   - with fix_knowledge() -> blocchi di codice che permettono di scrivere codice privo di reasoning
# - magie sintattiche
#   - _x == 2 -> Equals(_x, 2)
#   - _x + 3 -> qualche oggetto che restituisce x + 3 quando il valore di x è noto (tipo il sistema può chiamare "evaluate"? anzi no! evaluators!)
#   - A & B -> e compagnia bella
#   - if A -> usare direttamente una Expression come bool
#   - for s in A -> iterare direttamente per ottenere tutte le sostituzioni che soddisfano una formula
#   - with assumptions(...) -> aggiunge **temporaneamente** alla KB del contesto corrente delle formule
# - listener nel CognitiveSystem -> possono evitare che una cosa sia salvata nella KB
# - cut?
