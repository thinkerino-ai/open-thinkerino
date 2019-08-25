import typing
from collections import deque
from typing import Optional, Iterable, Set

from aitools.logic import Expression, Substitution
from aitools.proofs.context import contextual
from aitools.proofs.proof import Prover, Proof, ProofSet
from aitools.proofs.provers import KnowledgeRetriever, RestrictedModusPonens


class KnowledgeBase:
    def __init__(self):
        self.__known_formulas: Set[Expression] = set()
        self.__provers: Set[Prover] = set()

        self.__initialize_default_provers()

    def __initialize_default_provers(self):
        self.__provers.add(KnowledgeRetriever())
        # although it's quite a standard proving strategy, I really don't like having MP as a default...
        self.__provers.add(RestrictedModusPonens())

    def retrieve(self, formula: Optional[Expression] = None) -> Iterable[Substitution]:
        """Retrieves all formula from the KnowledgeBase which are unifiable with the given one.
        No proofs are searched, so either a formula is **IN** the KB, or nothing will be returned"""
        for expr in self.__known_formulas:
            subst = Substitution.unify(expr, formula) if formula is not None else Substitution()

            if subst is not None:
                yield subst

    def add_formulas(self, *formulas: Expression):
        """Adds all of the given formulas to the currently known formulas."""
        for f in formulas:
            if not isinstance(f, Expression):
                raise TypeError("Only formulas can be added to a Knowledge Base!")
            self.__known_formulas.add(f)

    def prove(self, formula: Expression, truth: bool = True) -> ProofSet:

        """Backward search to prove a given formulas using all known provers"""
        proof_sources: typing.Deque[Iterable[Proof]] = deque(
            prover(formula, _kb=self, _truth=truth) for prover in self.__provers
        )

        _embedded_prover: Prover = getattr(formula, '_embedded_prover', None)
        if _embedded_prover is not None:
            proof_sources.appendleft(_embedded_prover(formula=formula, _kb=self, _truth=truth))

        @contextual('kb', self)
        def _inner():
            while any(proof_sources):
                source = proof_sources.popleft().__iter__()
                try:
                    new_proof = next(source)
                except StopIteration:
                    pass
                else:
                    proof_sources.append(source)
                    yield new_proof

        return ProofSet(_inner())
