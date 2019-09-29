import typing
from collections import deque
from typing import Set, Collection, Optional, Iterable, Union, Deque

import ZODB

from aitools.logic import Expression, Substitution
from aitools.logic.utils import normalize_variables, VariableSource
from aitools.proofs.context import contextual
from aitools.proofs.knowledge_bases.knowledge_base import KnowledgeBase
from aitools.proofs.listeners import Listener, _MultiListenerWrapper
from aitools.proofs.proof import Prover, ProofSet, Proof
from aitools.proofs.provers import KnowledgeRetriever, RestrictedModusPonens
from aitools.proofs.utils import EmbeddedProver


class ZodbPersistentKnowledgeBase(KnowledgeBase):

    def __init__(self, *, storage=None):
        self.db = ZODB.DB(storage)

        self._initialize_db()

        self.__provers: Set[Prover] = set()
        self._listeners: Set[Listener] = set()
        # TODO switch to a custom collection with limited capacity, to avoid infinite growth
        self._temporary_listeners: Collection[Listener] = set()

        self.__variable_source = VariableSource()
        super().__init__()

    @property
    def _variable_source(self):
        return self.__variable_source

    @property
    def _provers(self):
        return self.__provers

    def _initialize_db(self):
        with self.db.transaction("initializing db if necessary") as conn:
            if 'known_formulas' not in conn.root():
                conn.root.known_formulas = set()

    def retrieve(self, formula: Optional[Expression] = None, *, previous_substitution: Substitution = None) -> Iterable[Substitution]:
        # TODO index! indeeeeeex! INDEEEEEEX! I N D E E E E E E E X ! ! ! ! !
        with self.db.transaction() as conn:
            for expr in conn.root.known_formulas:
                subst = Substitution.unify(normalize_variables(expr), formula, previous=previous_substitution) if formula is not None else Substitution()

                if subst is not None:
                    yield subst

    def _add_formulas(self, *formulas: Expression):
        with self.db.transaction() as conn:
            for f in formulas:
                conn.root.known_formulas.add(f)
            conn.root._p_changed__ = True

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
        with self.db.transaction() as conn:
            return len(conn.root.known_formulas)
