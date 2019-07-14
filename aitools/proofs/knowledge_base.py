from typing import List, Optional, Iterable, Set

from aitools.logic import Expression, Substitution


class KnowledgeBase():
    def __init__(self):
        self.__known_formulas: Set[Expression] = set()

    def retrieve(self, unifying_with: Optional[Expression] = None) -> Iterable[Substitution]:
        """Retrieves a formula from the KnowledgeBase, possibly performing unification.
        No proofs are searched, so either the formula is **IN** the KB, or nothing will be returned"""
        for expr in self.__known_formulas:
            subst = Substitution.unify(expr, unifying_with) if unifying_with is not None else Substitution()

            if subst is not None:
                yield subst

    def add_formulas(self, *formulas: Iterable[Expression]):
        for f in formulas:
            self.__known_formulas.add(f)
