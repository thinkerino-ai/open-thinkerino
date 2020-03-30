import pickle
from collections import OrderedDict
from typing import Optional, Iterable, Set, Collection

import redis

from aitools.logic import Expression, Substitution, Variable
from aitools.logic.utils import VariableSource, normalize_variables
from aitools.proofs.index import make_key
from aitools.utils.abstruse_index import TrieIndex, AbstruseIndex
from aitools.proofs.knowledge_bases.knowledge_base import KnowledgeBase
from aitools.proofs.listeners import Listener
from aitools.proofs.proof import Prover

# TODO:
## - sbaglio a passare il level, nella versione senza redis chiamo solo una volta il costruttore per un nodo ma nella
##   versione con redis lo devo chiamare due volte (una è la stessa di prima, l'altra è per il fetch); al momento passo
##   il level come una cosa da propagare, ma forse dovrei semplicemente SALVARE ANCHE IL LIVELLO NEL DB


def pDict_class(db: redis.Redis, parent, dict_key_format, element_constructor):
    # key by which the dict will be stored
    redis_dict_key = dict_key_format.format(parent.id)

    class pDict:
        def keys(self):
            yield from db.hkeys(redis_dict_key)

        def items(self):
            yield from ((key, element_constructor(db=db, key=db.hget(redis_dict_key, repr(key)),
                                                  level=parent.level if hasattr(parent, 'level') else ...))
                        for key in db.hkeys(redis_dict_key))

        def values(self):
            yield from (val for key, val in self.items())

        def __iter__(self):
            yield from self.keys()

        def __contains__(self, key):
            return db.hexists(redis_dict_key, repr(key))

        def __getitem__(self, key):
            return element_constructor(
                db=db,
                key=db.hget(redis_dict_key, repr(key)),
                level=parent.level if hasattr(parent, 'level') else ...
            )

        def __setitem__(self, key, pSquare):
            return db.hset(redis_dict_key, repr(key), pSquare.id)

    return pDict


def pSet_class(db: redis.Redis, parent, set_key_format, element_constructor, extra_storage_steps=None):
    # key by which the pSet is saved
    redis_set_key = set_key_format.format(parent.id)

    class pSet:
        def add(self, obj):
            res = db.sadd(redis_set_key, obj.id)
            if extra_storage_steps is not None:
                extra_storage_steps(db=db, parent=parent, obj=obj)
            return res

        def __contains__(self, obj):
            return db.sismember(redis_set_key, obj.id)

        def __iter__(self):
            for key in db.sscan_iter(redis_set_key):
                yield element_constructor(db=db, key=key, level=parent.level if hasattr(parent, 'level') else ...)

        def __len__(self):
            return db.scard(redis_set_key)

    return pSet


def make_pickle_store(key_format):
    def pickle_store(db: redis.Redis, parent, obj):
        return db.set(key_format.format(obj.id), pickle.dumps(obj))
    return pickle_store


def make_unpickle_constructor(key_format):
    def unpickle_constructor(db, key, level):
        return pickle.loads(db.get(key_format.format(key.decode())))
    return unpickle_constructor


class IndexedRedisPersistenceKnowledgeBase(KnowledgeBase):

    def __init__(self, **kwargs):
        kb = self
        self.db = redis.Redis(**kwargs)

        self.__provers: Set[Prover] = set()
        self._listeners: Set[Listener] = set()
        # TODO switch to a custom collection with limited capacity, to avoid infinite growth
        self._temporary_listeners: Collection[Listener] = set()

        self.__variable_source = VariableSource()

        # TODO rename these classes :P
        class pCircle(AbstruseIndex):
            __last_id = 0

            def __init__(self, level, id_=None, **__):
                if id_ is None:
                    self.id = pCircle.__last_id
                    pCircle.__last_id += 1
                else:
                    self.id = id_

                super().__init__(
                    level=level,
                    subindex_class=pSquare,
                    # wow, just wow o.o such complicated
                    object_container_class=pSet_class(
                        db=kb.db,
                        parent=self,
                        set_key_format='pCircle-formulas-{}',
                        element_constructor=make_unpickle_constructor('pFormula-{}'),
                        extra_storage_steps=make_pickle_store('pFormula-{}')
                    )
                )

            @property
            def subindex_tree(self):
                raw_square_id = kb.db.get('pCircle-square-{}'.format(self.id))
                square_id = int(raw_square_id) if raw_square_id is not None else None
                res = pSquare(id_=square_id)

                if square_id is None:
                    kb.db.set('pCircle-square-{}'.format(self.id), res.id)

                return res

        class pSquare(TrieIndex):
            __last_id = 0

            def __init__(self, id_=None, **__):
                if id_ is None:
                    self.id = pSquare.__last_id
                    pSquare.__last_id += 1
                else:
                    self.id = id_

                super().__init__(
                    subindex_container_class=pDict_class(
                        db=kb.db,
                        parent=self,
                        dict_key_format='pSquare-squares-{}',
                        element_constructor=lambda db, key, level: pSquare(id_=key)
                    ),
                    object_container_class=pSet_class(
                        db=kb.db,
                        parent=self,
                        set_key_format='pSquare-circles-{}',
                        element_constructor=lambda db, key, level: pCircle(level=level, id_=key)
                    )
                )

            def add_object(self, obj):
                self.objects.add(obj)

        self._known_formulas = pCircle(level=0)
        super().__init__()

    @property
    def _variable_source(self):
        return self.__variable_source

    @property
    def _provers(self):
        return self.__provers

    def retrieve(self, formula: Optional[Expression] = None, *, previous_substitution: Substitution = None) -> Iterable[Substitution]:
        key = make_key(formula)
        for f in self._known_formulas.retrieve(key):
            f = normalize_variables(f)
            subst = Substitution.unify(formula, f, previous=previous_substitution)
            if subst is not None:
                yield subst

    def _add_formulas(self, *formulas: Expression):
        for f in formulas:
            key = make_key(f)
            self._known_formulas.add(key)

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
        key = make_key(Variable())
        return len(list(self._known_formulas.retrieve(key)))

