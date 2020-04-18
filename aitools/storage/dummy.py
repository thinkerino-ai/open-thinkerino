from typing import Set, Iterable, Tuple, cast, Dict

from aitools.logic import LogicObject, Substitution
from aitools.storage.base import LogicObjectStorage
from aitools.storage.index import make_key, TrieIndex, AbstruseIndex, AbstruseKey, AbstruseKeyElement


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
        self.subindices: Dict[AbstruseKeyElement, DummyTrieIndex] = dict()
        self.objects: Set[DummyAbstruseIndex] = set()

    def make_node(self):
        return DummyTrieIndex()

    def _get_or_create_subindex(self, key_element) -> TrieIndex:
        if key_element not in self.subindices:
            self.subindices[key_element] = self.make_node()
        subindex: TrieIndex = self.subindices[key_element]
        return subindex

    def _get_all_subindices(self):
        return self.subindices.values()

    def _get_all_keys_and_subindices(self):
        return self.subindices.items()

    def _get_subindex_by_key_element(self, key_element: AbstruseKeyElement) -> TrieIndex:
        return self.subindices.get(key_element)

    def _maybe_store_object(self, obj):
        if obj not in self.objects:
            self.objects.add(obj)

    def _get_all_objects(self):
        return iter(self.objects)


class DummyAbstruseIndex(AbstruseIndex):

    def __init__(self, *, level=0):
        super().__init__(level=level)
        self.objects = set()
        self._subindex_tree = DummyTrieIndex()

    def make_node(self, *, new_level):
        return DummyAbstruseIndex(level=new_level)

    def _get_all_objects(self):
        return self.objects

    def _maybe_store_object(self, obj):
        if obj not in self.objects:
            self.objects.add(obj)

    @property
    def subindex_tree(self):
        return self._subindex_tree

class DummyIndexedLogicObjectStorage(LogicObjectStorage):

    def __init__(self):
        self._objects: DummyAbstruseIndex[LogicObject] = DummyAbstruseIndex()

    def add(self, *objects: LogicObject):
        for obj in objects:
            key: AbstruseKey[LogicObject] = make_key(obj)
            self._objects.add(key=key, obj=obj)

    def search_unifiable(self, other: LogicObject) -> Iterable[Tuple[LogicObject, Substitution]]:
        key: AbstruseKey[LogicObject] = make_key(other)
        for obj in self._objects.retrieve(key):
            unifier = Substitution.unify(obj, other)
            if unifier is not None:
                yield obj, unifier

    def __len__(self):
        return sum(1 for _ in self._objects.retrieve([[None]]))
