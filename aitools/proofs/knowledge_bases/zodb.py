import collections
from typing import Set, Collection, Optional, Iterable, Iterator

import ZODB
from persistent import Persistent
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping

from aitools.logic import Expression, Substitution, Variable
from aitools.logic.utils import normalize_variables, VariableSource
from aitools.proofs.index import make_key
from aitools.utils.abstruse_index import TrieIndex, AbstruseIndex
from aitools.proofs.knowledge_bases.knowledge_base import KnowledgeBase
from aitools.proofs.listeners import Listener
from aitools.proofs.proof import Prover


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
        with self.db.transaction() as conn:
            for expr in conn.root.known_formulas:
                subst = Substitution.unify(normalize_variables(expr), formula, previous=previous_substitution) if formula is not None else Substitution()

                if subst is not None:
                    yield subst

    def _add_formulas(self, *formulas: Expression):
        with self.db.transaction() as conn:
            for f in formulas:
                conn.root.known_formulas.add(f)
            conn.root._p_changed = True

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


class _Set(collections.abc.MutableSet):
    def __init__(self, iterable=()):
        self.container = set(iterable)
        self.closure = None

    def add(self, x) -> None:
        self.container.add(x)
        self.closure._p_changed = True

    def discard(self, x) -> None:
        self.container.discard(x)
        self.closure._p_changed = True

    def __contains__(self, x: object) -> bool:
        return self.container.__contains__(x)

    def __len__(self) -> int:
        return len(self.container)

    def __iter__(self) -> Iterator:
        return self.container.__iter__()


# TODO I'm sure I could refactor everything in a "Storage" class so that persistence becomes actually an injected dependency
class _PersistentAbstruseIndex(Persistent, AbstruseIndex):
    def __init__(self, *args, **kwargs):
        objects = _Set()
        objects.closure = self
        kwargs.update(subindex=_PersistentTrieIndex(), object_container=objects)
        super().__init__(*args, **kwargs)

    def make_node(self, *, new_level):
        return _PersistentAbstruseIndex(level=new_level)


class _ListObjectContainer(collections.abc.MutableSet):
    def __init__(self, iterable=()):
        self.container = PersistentList(iterable)

    def add(self, x) -> None:
        self.container.append(x)

    def discard(self, x) -> None:
        self.container.remove(x)

    def __contains__(self, x: object) -> bool:
        return self.container.__contains__(x)

    def __len__(self) -> int:
        return len(self.container)

    def __iter__(self) -> Iterator:
        return self.container.__iter__()


class _PersistentTrieIndex(Persistent, TrieIndex):
    def __init__(self):
        super().__init__(subindex_container=PersistentMapping(), object_container=_ListObjectContainer())

    def make_node(self):
        return _PersistentTrieIndex()


# TODO ok it is evident I don't know how to use ZODB :P
class IndexedZodbPersistenceKnowledgeBase(ZodbPersistentKnowledgeBase):
    def _initialize_db(self):
        with self.db.transaction("initializing db if necessary") as conn:
            if 'known_formulas' not in conn.root():
                conn.root.known_formulas = _PersistentAbstruseIndex()

    def retrieve(self, formula: Optional[Expression] = None, *, previous_substitution: Substitution = None) -> Iterable[Substitution]:
        result = []
        with self.db.transaction() as conn:
            key = make_key(formula)
            for expr in list(conn.root.known_formulas.retrieve(key)):
                subst = Substitution.unify(normalize_variables(expr), formula, previous=previous_substitution) \
                    if formula is not None else Substitution()

                if subst is not None:
                    result.append(subst)
        # TODO investigate why I had to do this, I think it has to do with yield within a transaction, but who knows :P
        return result

    def _add_formulas(self, *formulas: Expression):
        with self.db.transaction() as conn:
            for f in formulas:
                key = make_key(f)
                conn.root.known_formulas.add(key, f)

    def __len__(self):
        with self.db.transaction() as conn:
            key = make_key(Variable())
            return len(list(conn.root.known_formulas.retrieve(key)))
