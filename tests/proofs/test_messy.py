import pytest

from aitools.logic import Variable, Substitution, Expression
from aitools.logic.utils import subst, constants, wrap, VariableSource
from aitools.proofs.language import Implies, MagicPredicate, Not, And, Or
from aitools.proofs.proof import Proof
from aitools.proofs.provers import KnowledgeRetriever, NegationProver, DeclarativeProver
from aitools.proofs.utils import predicate_function


def test_retrieve_known_formula(test_knowledge_base):
    # TODO this now is more or less duplicated in test_storage, I need to decide what to do with it

    IsA, dylan, cat = constants('IsA, dylan, cat')
    test_knowledge_base.add_formulas(IsA(dylan, cat))
    # we can retrieve it because we already know it
    substitutions = list(test_knowledge_base.retrieve(IsA(dylan, cat)))

    assert len(substitutions) == 1
    assert all(isinstance(s, Substitution) for s in substitutions)


def test_retrieve_known_formula_transactional(test_knowledge_base):
    if not test_knowledge_base.supports_transactions():
        pytest.skip("KB implementation doesn't support transactions")

    IsA, dylan, cat = constants('IsA, dylan, cat')

    with test_knowledge_base.transaction():
        test_knowledge_base.add_formulas(IsA(dylan, cat))

    substitutions = list(test_knowledge_base.retrieve(IsA(dylan, cat)))

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

    substitutions = list(test_knowledge_base.retrieve(IsA(dylan, cat)))
    assert len(substitutions) == 0


def test_retrieve_known_open_formula(test_knowledge_base):
    # TODO this now is more or less duplicated in test_storage, I need to decide what to do with it
    v = VariableSource()

    IsA, dylan, cat, hugo = constants('IsA, dylan, cat, hugo')

    test_knowledge_base.add_formulas(
        IsA(dylan, cat),
        IsA(hugo, cat)
    )

    substitutions = list(test_knowledge_base.retrieve(IsA(v._x, cat)))
    assert len(substitutions) == 2

    assert all(isinstance(s, Substitution) for s in substitutions)

    assert any(substitution.get_bound_object_for(v._x) == dylan for substitution in substitutions)
    assert any(substitution.get_bound_object_for(v._x) == hugo for substitution in substitutions)


def test_open_formulas_added_only_once(test_knowledge_base):
    # TODO this now is more or less duplicated in test_storage, I need to decide what to do with it
    v = VariableSource()

    Foo, a, b = constants('Foo, a, b')

    test_knowledge_base.add_formulas(Foo(a, b), Foo(v.x, v.y), Foo(v.x, v.x), Foo(v.w, v.z))

    assert len(test_knowledge_base) == 3


def test_formulas_are_be_normalized(test_knowledge_base):
    v = VariableSource()

    Foo, Bar, Baz, a, b = constants('Foo, Bar, Baz, a, b')

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

    test_knowledge_base.add_formulas(
        IsNatural(wrap(0)),
        IsNatural(v.x) << Implies >> IsNatural(successor(v.x))
    )

    baseline_proofs = list(test_knowledge_base.prove(IsNatural(successor(wrap(0)))))
    assert any(baseline_proofs)

    # actual test
    proofs = list(test_knowledge_base.prove(IsNatural(successor(successor(wrap(0))))))
    assert any(proofs)


def _is_known_formula_proof_of(proof: Proof, formula: Expression) -> bool:
    return (isinstance(proof, Proof) and not any(proof.premises) and
            isinstance(proof.inference_rule, KnowledgeRetriever) and
            proof.substitution.apply_to(formula) == proof.substitution.apply_to(proof.conclusion))


def test_proof_known_formula(test_knowledge_base):
    IsA, dylan, cat = constants('IsA, dylan, cat')

    test_knowledge_base.add_formulas(IsA(dylan, cat))

    target = IsA(dylan, cat)
    proofs = list(test_knowledge_base.prove(target))

    # at least one way to prove it directly!
    assert all(_is_known_formula_proof_of(p, target) for p in proofs)
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
    assert all(_is_known_formula_proof_of(proof, target) for proof in proofs)

    assert any(p.substitution.get_bound_object_for(v._x) == dylan for p in proofs)
    assert any(p.substitution.get_bound_object_for(v._x) == hugo for p in proofs)


def test_implication_shortcut():
    v = VariableSource()
    IsA, cat, animal = constants('IsA, cat, animal')
    assert (IsA(v._x, cat) << Implies >> IsA(v._x, animal)) == (Implies(IsA(v._x, cat), IsA(v._x, animal)))


def test_simple_deduction(test_knowledge_base):
    v = VariableSource()

    IsA, cat, animal, dylan = constants('IsA, cat, animal, dylan')

    test_knowledge_base.add_formulas(
        IsA(v._x, cat) << Implies >> IsA(v._x, animal)
    )

    test_knowledge_base.add_formulas(IsA(dylan, cat))

    proofs = list(test_knowledge_base.prove(IsA(dylan, animal)))
    assert any(proofs)
    assert all(isinstance(p, Proof) for p in proofs)


def test_deduction_chain(test_knowledge_base):
    v = VariableSource()

    IsA, cat, mammal, animal, dylan = constants('IsA, cat, mammal, animal, dylan')

    test_knowledge_base.add_formulas(
        IsA(v._x, cat) << Implies >> IsA(v._x, mammal),
        IsA(v._x, mammal) << Implies >> IsA(v._x, animal),
        IsA(dylan, cat)
    )

    proofs = list(test_knowledge_base.prove(IsA(dylan, animal)))

    assert any(proofs)

    assert len(proofs[0].premises) > 0


@predicate_function
def IsEven(n: int):
    if n % 2 == 0:
        return True
    else:
        return False


def test_simple_custom_prover_passing_python_value(test_knowledge_base):
    assert any(test_knowledge_base.prove(IsEven(2)))

    # this means we can't prove it, not that we can prove it is false
    assert not any(test_knowledge_base.prove(IsEven(3)))


def test_simple_custom_prover_to_be_false(test_knowledge_base):
    # now *this* means that we can prove it is false :P
    assert any(test_knowledge_base.prove(IsEven(3), truth=False))


@predicate_function
def IsMultipleOf4(n: int):
    from aitools.proofs.context import prove
    if prove(IsEven(n // 2)):
        return True
    elif prove(IsEven(n // 2), truth=False):
        return False


@pytest.mark.xfail(reason="This needs to be implemented, but it's too complex for my little sleepy brain right now :P")
def test_custom_prover_chain_adds_premises(test_knowledge_base):
    proofs = list(test_knowledge_base.prove(IsMultipleOf4(20)))
    assert len(proofs[0].premises) > 0


def test_custom_prover_chain(test_knowledge_base):
    proofs = list(test_knowledge_base.prove(IsMultipleOf4(20)))
    assert any(proofs)

    # this means we can't prove it, not that we can prove it is false
    assert not any(test_knowledge_base.prove(IsMultipleOf4(14)))


def test_custom_prover_in_open_formula(test_knowledge_base):
    v = VariableSource()

    IsNice = MagicPredicate()

    # I don't actually like even numbers, unless they are powers of 2
    test_knowledge_base.add_formulas(IsEven(v._x) << Implies >> IsNice(v._x))

    # ok maybe this IS necessary :P otherwise the test_knowledge_base doesn't know how to use it
    test_knowledge_base.add_provers(IsEven)

    assert any(test_knowledge_base.prove(IsNice(32)))


def test_custom_prover_with_explicit_formula(test_knowledge_base):
    v = VariableSource()

    IsPayload = MagicPredicate()

    @predicate_function(proves=IsPayload(v._x))
    def name_here_does_not_matter(x: dict):
        return isinstance(x, dict) and isinstance(x['code'], int) and isinstance(x['message'], str)

    test_knowledge_base.add_provers(name_here_does_not_matter)

    assert any(test_knowledge_base.prove(
        IsPayload({'code': 200, 'message': 'success!'})
    ))


def test_custom_prover_incomplete(test_knowledge_base):
    # this prover can only prove its formula in some cases
    @predicate_function
    def IsPrime(n: int):
        if n in (2, 3, 5, 7):
            return True
        if n in (4, 6, 8):
            return False
        # None means "Who knows?"
        return None

    test_knowledge_base.add_provers(NegationProver())

    assert any(test_knowledge_base.prove(IsPrime(2)))
    assert any(test_knowledge_base.prove(Not(IsPrime(4))))
    assert not any(test_knowledge_base.prove(IsPrime(10)))
    assert not any(test_knowledge_base.prove(Not(IsPrime(10))))


def test_multiple_custom_provers_for_the_same_formula(test_knowledge_base):
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

    test_knowledge_base.add_provers(prime_prover_012345, prime_prover_456789, NegationProver())

    assert any(test_knowledge_base.prove(IsPrime(2)))
    assert any(test_knowledge_base.prove(IsPrime(7)))
    assert any(test_knowledge_base.prove(Not(IsPrime(0))))
    assert any(test_knowledge_base.prove(Not(IsPrime(8))))

    assert len(list(test_knowledge_base.prove(IsPrime(5)))) == 2
    assert len(list(test_knowledge_base.prove(Not(IsPrime(4))))) == 2

    assert not any(test_knowledge_base.prove(IsPrime(11)))
    assert not any(test_knowledge_base.prove(Not(IsPrime(11))))


def test_prover_returning_substitutions(test_knowledge_base):
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

    assert (test_knowledge_base.prove(Likes("lisa", "nelson")))

    lisa_likes_proofs = list(test_knowledge_base.prove(Likes("lisa", v._y)))
    assert (len(lisa_likes_proofs) == 1)
    assert (any(p.substitution.get_bound_object_for(v._y) == 'nelson' for p in lisa_likes_proofs))

    likes_lisa_proofs = list(test_knowledge_base.prove(Likes(v._y, "lisa")))
    assert (len(likes_lisa_proofs) == 1)
    assert (any(p.substitution.get_bound_object_for(v._y) == "milhouse") for p in lisa_likes_proofs)

    # nobody likes milhouse
    assert (not any(test_knowledge_base.prove(Likes(v._y, "milhouse"))))


def test_prover_returning_substitution_false(test_knowledge_base):
    v = VariableSource()

    @predicate_function
    def Likes(_x, _y):
        if _x == "lisa" and isinstance(_y, Variable):
            return False, subst((wrap("milhouse"), [_y]))

        return None

    test_knowledge_base.add_provers(NegationProver())

    assert not any(test_knowledge_base.prove(Likes("lisa", "milhouse")))

    assert any(test_knowledge_base.prove(Not(Likes("lisa", v._y))))


def test_prover_returning_multiple_results(test_knowledge_base):
    v = VariableSource()

    @predicate_function
    def In(_x, _collection):

        if isinstance(_x, Variable):
            for el in _collection:
                yield subst((wrap(el), [_x]))
        else:
            yield _x in _collection

    test_knowledge_base.add_provers(NegationProver())

    assert any(test_knowledge_base.prove(In(3, [1, 2, 3])))
    assert any(test_knowledge_base.prove(Not(In(4, [1, 2, 3]))))

    assert not any(test_knowledge_base.prove(In(4, [1, 2, 3])))
    assert not any(test_knowledge_base.prove(Not(In(3, [1, 2, 3]))))

    assert len(list(test_knowledge_base.prove(In(v._x, [1, 2, 3])))) == 3


def test_declarative_provers_as_provers(test_knowledge_base):
    v = VariableSource()

    IsNumber, IsOdd, seven = constants("IsNumber, IsOdd, seven")

    binary_conjunction = DeclarativeProver(
        premises=[v.A, v.B],
        conclusions=[And(v.A, v.B)]
    )

    # ugly ugly ugly :P
    binary_disjunction_1 = DeclarativeProver(
        premises=[v.A],
        conclusions=[Or(v.A, v.B)]
    )
    binary_disjunction_2 = DeclarativeProver(
        premises=[v.B],
        conclusions=[Or(v.A, v.B)]
    )

    test_knowledge_base.add_provers(binary_conjunction, binary_disjunction_1, binary_disjunction_2)

    test_knowledge_base.add_formulas(IsNumber(seven), IsOdd(seven))

    proofs = list(test_knowledge_base.prove(And(IsNumber(seven), Or(IsEven(seven), IsOdd(seven)))))

    assert any(proofs)


@pytest.mark.xfail(reason="Sorry, but I'm lazy and I lost interest in this part :P")
def test_declarative_provers_as_listeners(test_knowledge_base):
    v = VariableSource()

    IsNumber, IsOdd, seven = constants("IsNumber, IsOdd, seven")

    binary_conjunction = DeclarativeProver(
        premises=[v.A, v.B],
        conclusions=[And(v.A, v.B)]
    )

    # ugly ugly ugly :P
    binary_disjunction_1 = DeclarativeProver(
        premises=[v.A],
        conclusions=[Or(v.A, v.B)]
    )
    binary_disjunction_2 = DeclarativeProver(
        premises=[v.B],
        conclusions=[Or(v.A, v.B)]
    )

    test_knowledge_base.add_listeners(binary_conjunction, binary_disjunction_1, binary_disjunction_2)

    test_knowledge_base.add_formulas(IsNumber(seven), IsOdd(seven))

    proofs_conjunction_1 = test_knowledge_base.prove(And(IsNumber(seven), IsOdd(seven)))
    proofs_conjunction_2 = test_knowledge_base.prove(And(IsOdd(seven), IsNumber(seven)))
    # is this even correct to have?
    proofs_conjunction_3 = test_knowledge_base.prove(And(IsNumber(seven), IsNumber(seven)))

    proofs_disjunction_1 = test_knowledge_base.prove(Or(IsOdd(seven), IsEven(seven)))
    proofs_disjunction_2 = test_knowledge_base.prove(Or(IsEven(seven), IsOdd(seven)))
    # again: do I really want this?
    proofs_disjunction_3 = test_knowledge_base.prove(Or(IsOdd(seven), IsOdd(seven)))

    assert any(proofs_conjunction_1)
    assert any(proofs_conjunction_2)
    assert any(proofs_conjunction_3)
    assert any(proofs_disjunction_1)
    assert any(proofs_disjunction_2)
    assert any(proofs_disjunction_3)

# altri casi:
# - evaluator (come il prover, ma restituisce un valore/oggetto anziché True/False/Substitution, oppure solleva
# eccezione se l'oggetto non è ancora abbastanza bound)
# - evaluator generato da un prover (simboli funzionali)
# - prover da un evaluator?
# - 0-step proof -> cose che so già senza dover ragionare
#   - with fix_knowledge() -> blocchi di codice che permettono di scrivere codice privo di reasoning
# - magie sintattiche
#   - _x == 2 -> Equals(_x, 2)
#   - _x + 3 -> qualche oggetto che restituisce x + 3 quando il valore di x è noto (tipo il sistema può chiamare
#   "evaluate"? anzi no! evaluators!)
#   - A & B -> e compagnia bella
#   - if A -> usare direttamente una Expression come bool
#   - for s in A -> iterare direttamente per ottenere tutte le sostituzioni che soddisfano una formula
#   - with assumptions(...) -> aggiunge **temporaneamente** alla KB del contesto corrente delle formule
# - listener nel CognitiveSystem -> possono evitare che una cosa sia salvata nella KB
# - cut?
