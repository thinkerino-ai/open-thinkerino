import typing
from collections import deque
from typing import Optional, Iterable, Set

from aitools.logic import Expression, Substitution, Variable
from aitools.logic.utils import normalize_variables, VariableSource
from aitools.proofs.index import make_key
from aitools.utils.abstruse_index import AbstruseIndex, TrieIndex
from aitools.proofs.knowledge_bases.knowledge_base import KnowledgeBase
from aitools.proofs.listeners import Listener
from aitools.proofs.proof import Prover


class DummyKnowledgeBase(KnowledgeBase):
    def __init__(self):
        self._known_formulas: Set[Expression] = set()
        self.__provers: Set[Prover] = set()
        self._listeners: Set[Listener] = set()
        # TODO switch to a custom collection with limited capacity, to avoid infinite growth
        self._temporary_listeners: typing.Collection[Listener] = set()

        self.__variable_source = VariableSource()
        super().__init__()

    @property
    def _variable_source(self):
        return self.__variable_source

    @property
    def _provers(self):
        return self.__provers

    def retrieve(self, formula: Optional[Expression] = None, *, previous_substitution: Substitution = None) -> Iterable[Substitution]:
        """Retrieves all formula from the KnowledgeBase which are unifiable with the given one.
        No proofs are searched, so either a formula is **IN** the KB, or nothing will be returned"""
        for expr in self._known_formulas:
            subst = Substitution.unify(normalize_variables(expr), formula, previous=previous_substitution) if formula is not None else Substitution()

            if subst is not None:
                yield subst

    def _add_formulas(self, *formulas: Expression):
        for f in formulas:
            self._known_formulas.add(f)

    def _add_prover(self, prover):
        self.__provers.add(prover)

    def _add_listener(self, listener: Listener, retroactive: bool = False, temporary=False):
        destination = self._listeners if not temporary else self._temporary_listeners
        destination.add(listener)

    def _get_listeners_for(self, formula: Expression, *, temporary=False):
        # TODO indexing (we already take the formula as input to that purpose)
        source = self._listeners if not temporary else self._temporary_listeners
        # TODO use an ordered data structure! this is like the inefficientest of inefficiencies
        for listener in sorted(source, key=lambda l: l.priority, reverse=True):
            yield listener

    def __len__(self):
        return len(self._known_formulas)


class DummyTrieIndex(TrieIndex):
    def __init__(self):
        super().__init__(subindex_container=dict(), object_container=set())

    def make_node(self):
        return DummyTrieIndex()


class DummyAbstruseIndex(AbstruseIndex):
    def __init__(self, *, level=0):
        super().__init__(level=level, object_container=set(), subindex=DummyTrieIndex())

    def make_node(self, *, new_level):
        return DummyAbstruseIndex(level=new_level)


class DummyIndexedKnowledgeBase(DummyKnowledgeBase):

    def __init__(self):
        super().__init__()
        self._known_formulas: DummyAbstruseIndex = DummyAbstruseIndex()

    def retrieve(self, formula: Optional[Expression] = None, *, previous_substitution: Substitution = None) -> Iterable[Substitution]:
        """Retrieves all formula from the KnowledgeBase which are unifiable with the given one.
        No proofs are searched, so either a formula is **IN** the KB, or nothing will be returned"""
        key = make_key(formula)
        for f in self._known_formulas.retrieve(key):
            f = normalize_variables(f)
            subst = Substitution.unify(formula, f, previous=previous_substitution)
            if subst is not None:
                yield subst

    def _add_formulas(self, *formulas: Expression):
        for f in formulas:
            key = make_key(f)
            self._known_formulas.add(key, f)

    def __len__(self):
        key = make_key(Variable())
        return len(list(self._known_formulas.retrieve(key)))
