import pickle
from contextlib import contextmanager
from typing import Iterable, Tuple

from aitools.logic import LogicObject, Substitution, Expression, Variable
from aitools.storage.base import LogicObjectStorage, NodeStorage
from aitools.storage.implementations.node_index import NodeStoringAbstruseIndex
from aitools.storage.index import AbstruseIndex, AbstruseKey, WILDCARD


def make_plain_key(formula: LogicObject) -> AbstruseKey[str]:
    res: AbstruseKey[str] = []

    def inner(_formula: LogicObject, level: int):
        if len(res) == level:
            res.append([])

        res_slice = res[level]

        if isinstance(_formula, Expression):
            res_slice.append(len(_formula.children))
            for child in _formula.children:
                inner(child, level + 1)
        elif isinstance(_formula, Variable):
            res_slice.append(WILDCARD)
        else:
            res_slice.append("#"+str(hash(_formula)))

    inner(formula, 0)
    return res


class PickleSerializingLogicObjectStorage(LogicObjectStorage):

    def __init__(self, storage: NodeStorage):
        self._node_storage = storage
        self._objects: AbstruseIndex = NodeStoringAbstruseIndex(
            storage_id=0,
            node_storage=storage
        )

    @contextmanager
    def transaction(self):
        with self._node_storage.transaction():
            yield

    def commit(self):
        self._node_storage.commit()

    def rollback(self):
        self._node_storage.rollback()

    def add(self, *objects: LogicObject):
        for obj in objects:
            key = make_plain_key(obj)
            self._objects.add(key=key, obj=pickle.dumps(obj))

    def search_unifiable(self, other: LogicObject) -> Iterable[Tuple[LogicObject, Substitution]]:
        key = make_plain_key(other)
        for obj_raw in self._objects.retrieve(key):
            obj = pickle.loads(obj_raw)
            unifier = Substitution.unify(obj, other)
            if unifier is not None:
                yield obj, unifier

    def __len__(self):
        return sum(1 for _ in self._objects.retrieve([[WILDCARD]]))
