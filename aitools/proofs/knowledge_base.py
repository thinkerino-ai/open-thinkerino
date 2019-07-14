import typing
from collections import deque
from typing import List, Optional, Iterable, Set

from aitools.logic import Expression, Substitution
from aitools.proofs.language import Formula
from aitools.proofs.proof import Prover, KnowledgeRetriever, Proof


class KnowledgeBase():
    def __init__(self):
        self.__known_formulas: Set[Formula] = set()
        self.__provers: Set[Prover] = set()

        self.__initialize_default_provers()

    def __initialize_default_provers(self):
        self.__provers.add(KnowledgeRetriever(self))

    def retrieve(self, formula: Optional[Expression] = None) -> Iterable[Substitution]:
        """Retrieves all formula from the KnowledgeBase which are unifiable with the given one.
        No proofs are searched, so either a formula is **IN** the KB, or nothing will be returned"""
        for expr in self.__known_formulas:
            subst = Substitution.unify(expr, formula) if formula is not None else Substitution()

            if subst is not None:
                yield subst

    def add_formulas(self, *formulas: Formula):
        """Adds all of the given formulas to the currently known formulas."""
        for f in formulas:
            if not isinstance(f, Formula):
                raise TypeError("Only formulas can be added to a Knowledge Base!")
            self.__known_formulas.add(f)

    def prove(self, formula: Formula) -> Iterable[Proof]:
        """Backward search to prove a given formulas using all known provers"""
        proof_sources: typing.Deque[Iterable[Proof]] = deque(prover(formula) for prover in self.__provers)

        while any(proof_sources):
            source = proof_sources.popleft()
            try:
                new_proof = next(source)
            except StopIteration:
                pass
            else:
                proof_sources.append(source)
                yield new_proof




