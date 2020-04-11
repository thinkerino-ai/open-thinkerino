from typing import Set, Iterable, Tuple

from aitools.logic import LogicObject, Substitution
from aitools.storage.base import LogicObjectStorage
from aitools.storage.index import make_key, TrieIndex, AbstruseIndex


class DummyLogicObjectStorage(LogicObjectStorage):
    def __init__(self):
        self._objects: Set[LogicObject] = set()

    def add(self, *objects: LogicObject):
        for obj in objects:
            self._objects.add(obj)

    def search_unifiable(self, other: LogicObject) -> Iterable[Tuple[LogicObject, Substitution]]:
        for obj in self._objects:
            unifier = Substitution.unify(obj, other)
            if unifier is not None:
                yield obj, unifier

    def __len__(self):
        return len(self._objects)


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


class DummyIndexedLogicObjectStorage(LogicObjectStorage):

    def __init__(self):
        self._objects: DummyAbstruseIndex = DummyAbstruseIndex()

    def add(self, *objects: LogicObject):
        for obj in objects:
            key = make_key(obj)
            self._objects.add(key=key, obj=obj)

    def search_unifiable(self, other: LogicObject) -> Iterable[Tuple[LogicObject, Substitution]]:
        key = make_key(other)
        for obj in self._objects.retrieve(key):
            unifier = Substitution.unify(obj, other)
            if unifier is not None:
                yield obj, unifier

    def __len__(self):
        return sum(1 for _ in self._objects.retrieve([[None]]))
