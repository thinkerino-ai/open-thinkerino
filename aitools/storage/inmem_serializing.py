import pickle
from typing import Dict, Set, Iterable, Tuple

from aitools.logic import LogicObject, Expression, Variable, Substitution
from aitools.storage.base import LogicObjectStorage
from aitools.storage.dummy import DummyAbstruseIndex
from aitools.storage.index import WILDCARD


class InMemSerializingLogicObjectStorage(LogicObjectStorage):
    def __init__(self):
        self._objects: Set[bytes] = set()

    def add(self, *objects: LogicObject):
        for obj in objects:
            self._objects.add(pickle.dumps(obj))

    def search_unifiable(self, other: LogicObject) -> Iterable[Tuple[LogicObject, Substitution]]:
        for s_obj in self._objects:
            obj = pickle.loads(s_obj)
            unifier = Substitution.unify(obj, other)
            if unifier is not None:
                yield obj, unifier

    def __len__(self):
        return len(self._objects)


def make_plain_key(formula: LogicObject):
    res = []

    def inner(formula, level):
        if len(res) == level:
            res.append([])

        if isinstance(formula, Expression):
            res[level].append(len(formula.children))
            for child in formula.children:
                inner(child, level + 1)
        elif isinstance(formula, Variable):
            res[level].append(WILDCARD)
        else:
            res[level].append(str(hash(formula)))

    inner(formula, 0)
    return res


class DummyIndexedSerializingLogicObjectStorage(LogicObjectStorage):

    def __init__(self):
        self._objects: DummyAbstruseIndex = DummyAbstruseIndex()

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
        return sum(1 for _ in self._objects.retrieve([[None]]))
