from aitools.logic import Variable, Substitution, LogicObject, Expression
from aitools.logic.utils import subst, logic_objects, variable_source as v
from aitools.proofs.knowledge_base import KnowledgeBase
from aitools.proofs.language import Implies
from aitools.proofs.proof import Proof
from aitools.proofs.provers import KnowledgeRetriever
from aitools.proofs.utils import predicate_function


def test_retrieve_known_formula():
    kb = KnowledgeBase()

    IsA, dylan, cat = logic_objects(3, clazz=LogicObject)

    kb.add_formulas(IsA(dylan, cat))

    # we can retrieve it because we already know it
    substitutions = list(kb.retrieve(IsA(dylan, cat)))

    assert any(substitutions)
    assert all(isinstance(s, Substitution) for s in substitutions)


def test_retrieve_known_open_formula():
    kb = KnowledgeBase()

    IsA, dylan, cat, hugo = logic_objects(4, clazz=LogicObject)

    kb.add_formulas(
        IsA(dylan, cat),
        IsA(hugo, cat)
    )

    substitutions = list(kb.retrieve(IsA(v._x, cat)))
    assert len(substitutions) == 2

    assert all(isinstance(s, Substitution) for s in substitutions)

    assert any(substitution.get_bound_object_for(v._x) == dylan for substitution in substitutions)
    assert any(substitution.get_bound_object_for(v._x) == hugo for substitution in substitutions)


def _is_known_formula_proof_of(proof: Proof, formula: Expression) -> bool:
    return (isinstance(proof, Proof) and not any(proof.premises) and
            isinstance(proof.inference_rule, KnowledgeRetriever) and
            proof.substitution.apply_to(formula) == proof.substitution.apply_to(proof.conclusion))


def test_proof_known_formula():

    kb = KnowledgeBase()

    IsA, dylan, cat = logic_objects(3, clazz=LogicObject)

    kb.add_formulas(IsA(dylan, cat))

    target = IsA(dylan, cat)
    proofs = list(kb.prove(target))

    # at least one way to prove it directly!
    assert all(_is_known_formula_proof_of(p, target) for p in proofs)
    assert any(proofs)


def test_proof_known_open_formula():
    # TODO maybe break this up in different tests with a single proof fixture?
    kb = KnowledgeBase()

    IsA, dylan, hugo, cat = logic_objects(4, clazz=LogicObject)

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
    IsA, cat, animal = logic_objects(3, clazz=LogicObject)
    assert (IsA(v._x, cat) <<Implies>> IsA(v._x, animal)) == (Implies(IsA(v._x, cat), IsA(v._x, animal)))


def test_simple_deduction():
    kb = KnowledgeBase()

    IsA, cat, animal, dylan = logic_objects(4, clazz=LogicObject)

    kb.add_formulas(
        IsA(v._x, cat) <<Implies>> IsA(v._x, animal)
    )

    kb.add_formulas(IsA(dylan, cat))

    proofs = list(kb.prove(IsA(dylan, animal)))
    assert any(proofs)
    assert all(isinstance(p, Proof) for p in proofs)


@predicate_function
def IsEven(n: int):
    if n % 2 == 0:
        return True
    else:
        return False


def test_simple_custom_prover_passing_python_value():
    kb = KnowledgeBase()

    assert any(kb.prove(IsEven(2)))

    # this means we can't prove it, not that we can prove it is false
    assert not any(kb.prove(IsEven(3)))


def test_simple_custom_prover_to_be_false():
    kb = KnowledgeBase()

    # now *this* means that we can prove it is false :P
    assert any(kb.prove(IsEven(3), truth=False))


@predicate_function
def IsMultipleOf4(n: int):
    from aitools.proofs.context import prove
    if prove(IsEven(n // 2)):
        return True
    elif prove(IsEven(n // 2), truth=False):
        return False


def test_custom_prover_chain():
    kb = KnowledgeBase()

    assert any(kb.prove(IsMultipleOf4(20)))

    # this means we can't prove it, not that we can prove it is false
    assert not any(kb.prove(IsMultipleOf4(14)))


def test_custom_prover_in_open_formula():
    kb = KnowledgeBase()


    # I don't actually like even numbers, unless they are powers of 2
    kb.add(IsEven(v._x) >> IsNice(v._x))

    assert any(kb.prove(IsNice(32)))


def test_custom_prover_with_explicit_formula():
    # TODO I don't like the input being a variable, but what else can I do?
    @predicate_function(proves=IsPayload(v._x))
    def name_here_does_not_matter(_x: dict):
        return isinstance(_x, dict) and isinstance(x['code'], int) and isinstance(x['message'], str)


    assert any(kb.prove(
        IsPayload({'code': 200, 'message': 'success!'})
    ))


def test_custom_prover_incomplete():
    # this prover can only prove its formula in some cases
    @predicate_function
    def IsPrime(_n: int):
        if _n in (2, 3, 5, 7):
            return True
        if _n in (4, 6, 8):
            return False
        # None means "Who knows?"
        return None

    kb = KnowledgeBase()


    assert any(kb.prove(IsPrime(2)))
    assert any(kb.prove(~IsPrime(4)))
    assert not any(kb.prove(IsPrime(10)))
    assert not any(kb.prove(~IsPrime(10)))


def test_multiple_custom_provers_for_the_same_formula():
    @predicate_function(proves=IsPrime(v._n))
    def prime_prover_012345(_n: int):
        if _n in (2, 3):
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

    kb = KnowledgeBase()


    assert any(kb.prove(IsPrime(2)))
    assert any(kb.prove(IsPrime(7)))
    assert any(kb.prove(~IsPrime(0)))
    assert any(kb.prove(~IsPrime(8)))

    assert len(list(kb.prove(IsPrime(5)))) == 2
    assert len(list(kb.prove(~IsPrime(4)))) == 2

    assert ~any(kb.prove(IsPrime(11)))
    assert ~any(kb.prove(~IsPrime(11)))


def test_prover_returning_substitutions():
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
            return True, subst(map[val], [var])

    kb = KnowledgeBase()

    assert (kb.prove(Likes("lisa", "nelson")))

    lisa_likes_proofs = kb.prove(Likes("lisa", v._y))
    assert (len(lisa_likes_proofs) == 1)
    assert (any(p.substitution.get_bound_object_for(v._y) == 'nelson' for p in lisa_likes_proofs))

    likes_lisa_proofs = kb.prove(Likes(v._y, "lisa"))
    assert (len(likes_lisa_proofs) == 1)
    assert (any(p.substitution.get_bound_object_for(v._y) == "milhouse") for p in lisa_likes_proofs)

    # nobody likes milhouse
    assert (not any(kb.prove(Likes(v._y, "milhouse"))))


def test_prover_returning_substitution_false():
    @predicate_function
    def Likes(_x, _y):
        if _x == "lisa" and isinstance(_y, Variable):
            return False, subst("milhouse", [_y])

        return None

    kb = KnowledgeBase()


    assert not any(kb.prove(Likes("lisa", "milhouse")))

    assert any(~Likes("lisa", _y))


def test_prover_returning_multiple_results():
    @predicate_function
    def In(_x, _collection):

        if isinstance(_x, Variable):
            for el in _collection:
                yield subst(el, [_x])
        else:
            return _x in _collection

    kb = KnowledgeBase()

    assert any(kb.prove(In(3, [1, 2, 3])))
    assert any(kb.prove(~In(4, [1, 2, 3])))

    assert not any(kb.prove(In(4, [1, 2, 3])))
    assert not any(kb.prove(~In(3, [1, 2, 3])))

    assert len(kb.prove(In(v._x, [1, 2, 3]))) == 3


def test_listener_simple_retroactive():
    triggered = False

    @listener(Is(v._x, cat))
    def deduce_meow(_x):
        nonlocal triggered
        triggered = True
        declare(Meows(_x))

    kb = KnowledgeBase()

    kb.add_listeners(deduce_meow)

    assert not triggered, "There is only the listener, it shouldn't have triggered"

    assert not any(kb.prove(Meows(dylan)))

    kb.add_formula(Is(dylan, cat))

    assert triggered, "The listener should have triggered retroactively!"

    assert any(kb.prove(Meows(dylan)))


def test_listener_simple_non_retroactive():
    triggered = False

    @listener(Is(v._x, cat), retroactive=False)
    def deduce_meow(_x):
        nonlocal triggered
        triggered = True
        declare(Meows(_x))

    kb = KnowledgeBase()

    kb.add_listeners(deduce_meow)

    assert not triggered, "There is only the listener, it shouldn't have triggered"

    assert not any(kb.prove(Meows(dylan)))

    kb.add_formula(Is(dylan, cat))

    assert not triggered, "The listener should **not** have triggered retroactively!"

    assert any(kb.prove(Meows(dylan)))

    assert triggered, "The listener should have triggered!"


def test_listener_complex_conjunction():
    @listener(IsParent(v._a, v._b), IsBrother(v._c, v._a))
    def deduce_uncle(_b, _c):
        # note that since we don't care for _a we don't ask for it!
        declare(IsUncle(_c, _b))

    kb = KnowledgeBase()

    kb.add_listeners(deduce_uncle)

    # TODO put checks about _temporary_listeners in a different test, for now I'm just writing things quickly
    assert len(kb._temporary_listeners) == 0

    kb.add_formulas(IsBrother(carl, alice))

    assert len(kb._temporary_listeners) == 1
    assert not any(kb.prove(IsUncle(carl, bob)))

    kb.add_formulas(IsParent(alice, bob))

    assert len(kb._temporary_listeners) == 0
    assert any(kb.prove(IsUncle(carl, bob)))


def test_listener_complex_disjunction():
    @listener(IsDog(v._x))
    @listener(IsBarkingHuman(v._x))
    def deduce_barks(_x):
        # yeah it's a stupid example, but I'm on a train and I'm quite drunk :P
        declare(Barks(_x))

    kb = KnowledgeBase()

    kb.add_listeners(deduce_barks)

    # if you ever heard The Fox: yep yep yep yep yep yepyep yepyep yepyep :P
    kb.add_formulas(IsDog(luce), IsBarkingHuman(bard))

    assert any(kb.prove(Barks(luce)))
    assert any(kb.prove(Barks(bard)))


def test_listener_manual_generation():
    @listener(v._formula)
    def deduce_uncle_but_in_a_weird_way(_formula):
        # this is one of the dumbest ways of doing it, but it shows what you can do with 'listen_for'
        subst = Substitution.unify(_formula, IsParent(v._a, v._b))
        if subst is not None:
            a = subst.get_bounded_object_for(v._a)
            b = subst.get_bounded_object_for(v._b)
            listen_for(
                IsBrother(v._c, a),
                lambda _c: declare(IsUncle(_c, b))
            )
            return

        subst = Substitution.unify(_formula, IsBrother(v._c, v._a))
        if subst is not None:
            c = subst.get_bounded_object_for(v._c)
            a = subst.get_bounded_object_for(v._a)
            listen_for(
                IsParent(a, v._b),
                lambda _b, _c: declare(IsUncle(c, _b))
            )

    with KnowledgeBase() as kb:

        kb.add_listeners(deduce_uncle_but_in_a_weird_way)
        kb.add_formula(IsParent(alice, bob))
        assert len(kb._temporary_listeners) == 1
        kb.add_formula(IsBrother(carl, alice))
        assert len(kb._temporary_listeners) == 0
        assert any(kb.prove(IsUncle(carl, bob)))

    with KnowledgeBase() as kb:

        kb.add_listeners(deduce_uncle_but_in_a_weird_way)
        kb.add_formula(IsBrother(carl, alice))
        assert len(kb._temporary_listeners) == 1
        kb.add_formula(IsParent(alice, bob))
        assert len(kb._temporary_listeners) == 0
        assert any(kb.prove(IsUncle(carl, bob)))


def test_listener_chain():
    @listener(A(v._x))
    def deduce_from_a_b(_x):
        declare(B(_x))

    @listener(B(v._x), retroactive=False)
    def deduce_from_b_c(_x):
        declare(C(_x))

    @listener(C(v._x))
    def deduce_from_c_d(_x):
        declare(D(_x))

    with KnowledgeBase() as kb:
        kb.add_listeners(deduce_from_b_c)
        kb.add_formula(A(foo))

        kb.add_listeners(deduce_from_a_b)
        kb.add_listeners(deduce_from_c_d)

        assert any(kb.prove(D(foo)))


def test_listener_priority():
    res = []

    @listener(Go, priority=1)
    def listener_1():
        res.append(1)

    # default priority is 0
    @listener(Go)
    def listener_0():
        res.append(0)

    @listener(Go, priority=2)
    def listener_2():
        res.append(2)

    with KnowledgeBase as kb:
        kb.add_listeners(listener_1, listener_0, listener_2)

        assert res == []

        kb.add_formula(Go)

        assert res == [2, 1, 0]


def test_listener_consume():
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

    with KnowledgeBase as kb:
        kb.add_listeners(consumer, other)
        assert not consumer_triggered and not other_triggered

        kb.add_formula(Go)
        assert consumer_triggered and not other_triggered

# altri casi:
# - evaluator (come il prover, ma restituisce un valore/oggetto anziché True/False/Substitution, oppure solleva eccezione se l'oggetto non è ancora abbastanza bound)
# - evaluator generato da un prover (simboli funzionali)
# - prover da un evaluator?
# - 0-step proof -> cose che so già senza dover ragionare
#   - with fix_knowledge() -> blocchi di codice che permettono di scrivere codice privo di reasoning
# - magie sintattiche
#   - declare(...) -> prende la KB corrente dal contesto e aggiunge le formule
#   - _x == 2 -> Equals(_x, 2)
#   - _x + 3 -> qualche oggetto che restituisce x + 3 quando il valore di x è noto (tipo il sistema può chiamare "evaluate"? anzi no! evaluators!)
#   - A & B -> e compagnia bella
#   - if A -> usare direttamente una Expression come bool
#   - for s in A -> iterare direttamente per ottenere tutte le sostituzioni che soddisfano una formula
#   - with assumptions(...) -> aggiunge **temporaneamente** alla KB del contesto corrente delle formule
# - listener nel CognitiveSystem -> possono evitare che una cosa sia salvata nella KB
# - cut?
