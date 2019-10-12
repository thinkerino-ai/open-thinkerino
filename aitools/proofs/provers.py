from typing import Iterable, List, Collection

from aitools.logic import Expression, Substitution
from aitools.logic.utils import VariableSource, normalize_variables
from aitools.proofs.language import Implies, Not
from aitools.proofs.proof import Prover, Proof


class KnowledgeRetriever(Prover):

    def __call__(self, formula: Expression, _kb=None, _truth: bool = True, _previous_substitution: Substitution = None):
        """Proves a formula to be true if it is found in the knowledge base"""
        for subst in _kb.retrieve(formula, previous_substitution=_previous_substitution):
            if _truth:
                yield Proof(inference_rule=self, conclusion=formula, substitution=subst)


class DeclarativeProver(Prover):
    def __init__(self, *, premises: Iterable[Expression], conclusions: Iterable[Expression], **kwargs):
        super().__init__(**kwargs)
        variable_mapping = {}
        # TODO investigate why these normalizations are necessary while the ones in __call__ don't change anything
        self.premises = tuple(normalize_variables(p, variable_mapping=variable_mapping) for p in premises)
        self.conclusions = tuple(normalize_variables(c, variable_mapping=variable_mapping) for c in conclusions)

    def __call__(self, formula: Expression, _kb=None, _truth: bool = True,
                 _previous_substitution: Substitution = None) -> Iterable[Proof]:
        # can only prove formulas to be true
        if _truth:
            variable_mapping = {}
            for conclusion in (normalize_variables(c, variable_mapping=variable_mapping) for c in self.conclusions):
                subst = Substitution.unify(formula, conclusion, previous=_previous_substitution)
                if subst is not None:
                    yield from self.__prove(_kb, conclusion, [normalize_variables(p, variable_mapping=variable_mapping)
                                                              for p in self.premises],
                                            previous_substitution=subst, premises=[])

    def __prove(self, kb, theorem: Expression, formulas: Collection[Expression], previous_substitution: Substitution,
                premises: List[Proof]):
        if len(formulas) == 0:
            yield Proof(inference_rule=self, conclusion=theorem, substitution=previous_substitution,
                        premises=tuple(premises))
        else:
            first, *rest = formulas
            for proof in kb.prove(first, previous_substitution=previous_substitution):
                yield from self.__prove(kb, theorem, rest, previous_substitution=previous_substitution,
                                        premises=premises+[proof])


class NegationProver(Prover):
    def __call__(self, formula: Expression, _kb=None, _truth: bool = True, _previous_substitution: Substitution = None):
        """Proves the negation of a formula to be True/False by proving the formula to be False/True (respectively)"""
        if formula.children[0] == Not and len(formula.children) == 2:
            for proof in _kb.prove(formula.children[1], not _truth, previous_substitution=_previous_substitution):
                yield Proof(inference_rule=self, conclusion=formula, substitution=proof.substitution, premises=(proof,))


class RestrictedModusPonens(Prover):
    """Restricted backward version of modus ponens, which won't perform recursive proof of implications.
    Also, it can only prove formulas to be True"""

    def __call__(self, formula: Expression, _kb=None, _truth: bool = True, _previous_substitution: Substitution = None):
        v = VariableSource()
        if _truth and isinstance(formula, Expression) and not formula.children[0] == Implies:
            rule_pattern = Implies(v._premise, formula)

            for rule_proof in _kb.prove(rule_pattern, previous_substitution=_previous_substitution):
                premise = rule_proof.substitution.get_bound_object_for(v._premise)
                for premise_proof in _kb.prove(premise, previous_substitution=rule_proof.substitution):
                    yield Proof(inference_rule=self, conclusion=formula, substitution=premise_proof.substitution,
                                premises=(rule_proof, premise_proof))
