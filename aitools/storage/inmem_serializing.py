from __future__ import annotations

import pickle
from typing import Dict, Set, Iterable, Tuple

from aitools.logic import LogicObject, Expression, Variable, Substitution
from aitools.storage.base import LogicObjectStorage
from aitools.storage.dummy import DummyAbstruseIndex
from aitools.storage.index import WILDCARD, AbstruseKey, AbstruseKeySlice, TrieIndex, AbstruseIndex, AbstruseKeyElement

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
            res_slice.append(str(hash(_formula)))

    inner(formula, 0)
    return res


class InMemSerializingAbstruseIndex(AbstruseIndex[LogicObject]):
    def __init__(self, *, storage_id, storage):
        super().__init__()  # TODO: remove
        self.id = storage_id
        self.storage: NodeStorage = storage
        self._subindex_tree = InMemSerializingTrieIndex(
            storage_id=storage.get_subindex_id_for_abstruse_node(self.id),
            storage=storage
        )

    @property
    def subindex_tree(self):
        return self._subindex_tree

    def make_node(self):
        return InMemSerializingAbstruseIndex(
            storage_id=self.storage.next_id(),
            storage=self.storage
        )

    def _get_all_objects(self) -> Iterable[T]:
        return (self.storage.get_object(_id) for _id in self.storage.get_all_object_ids_in_abstruse_node(self.id))

    def _maybe_store_object(self, obj):
        obj_id = self.storage.store_obj(obj)
        self.storage.store_object_for_abstruse_node(self.id, obj_id)


class InMemSerializingTrieIndex(TrieIndex[InMemSerializingAbstruseIndex]):
    def __init__(self, *, storage_id, storage):
        self.id = storage_id
        self.storage = storage

    def _maybe_store_object(self, obj: InMemSerializingAbstruseIndex):
        self.storage.store_abstruse_node_for_trie_index_id(self.id, obj.id)

    def _get_or_create_subindex(self, key_element) -> TrieIndex:
        index_id = self.storage.get_subindex_from_trie_by_key(self.id, key_element)

        if index_id is None:
            index_id = self.storage.next_id()
            self.storage.store_trie_subindex_for_trie_node_and_key(self.id, key_element, index_id)

        return InMemSerializingTrieIndex(
            storage_id=index_id,
            storage=self.storage
        )

    def make_node(self):
        return InMemSerializingTrieIndex(
            storage_id=self.storage.next_id(),
            storage=self.storage
        )

    def _get_all_objects(self):
        return (
            InMemSerializingAbstruseIndex(
                storage_id=obj_id,
                storage=self.storage
            )
            for obj_id in self.storage.get_all_object_ids_in_trie_node(self.id))

    def _get_all_subindices(self):
        return (
            InMemSerializingTrieIndex(storage_id=index_id, storage=self.storage)
            for index_id in self.storage.get_all_subindices_in_trie_node(self.id)
        )

    def _get_all_keys_and_subindices(self) -> Iterable[Tuple[AbstruseKeyElement, TrieIndex[T]]]:
        return (
            (key, InMemSerializingTrieIndex(storage_id=index_id, storage=self.storage))
            for key, index_id in self.storage.get_all_key_value_pairs_in_trie_node(self.id)
        )

    def _get_subindex_by_key_element(self, key_element: AbstruseKeyElement) -> TrieIndex[T]:
        index_id = self.storage.get_subindex_from_trie_by_key(self.id, key_element)
        if index_id is None:
            return None
        return InMemSerializingTrieIndex(storage_id=index_id, storage=self.storage)


class NodeStorage:
    def __init__(self):
        self.last_id = 0
        self.abstruse_nodes = {}
        self.trie_nodes = {}
        self.objects_by_id = {}
        self.objects_by_value = {}

    def next_id(self):
        self.last_id += 1
        return self.last_id

    def store_abstruse_node_for_trie_index_id(self, trie_id, abstruse_id):
        objects = self.__get_trie_node(trie_id)['objects']
        objects.add(abstruse_id)

    def get_all_object_ids_in_trie_node(self, id):
        for obj_id in self.__get_trie_node(id)['objects']:
            yield obj_id

    def __get_trie_node(self, trie_id):
        res = self.trie_nodes.get(trie_id)
        if res is None:
            res = dict(objects=set(), subindices={})
            self.trie_nodes[trie_id] = res

        return res

    def __get_abstruse_node(self, id):
        res = self.abstruse_nodes.get(id)
        if res is None:
            res = dict(objects=set(), subindex_id=self.next_id())
            self.abstruse_nodes[id] = res

        return res

    def get_object(self, id):
        return self.objects_by_id[id]

    def get_all_object_ids_in_abstruse_node(self, id):
        for obj_id in self.__get_abstruse_node(id)['objects']:
            yield obj_id

    def get_subindex_id_for_abstruse_node(self, id):
        return self.__get_abstruse_node(id)['subindex_id']

    def store_object_for_abstruse_node(self, id, obj_id):
        self.__get_abstruse_node(id)['objects'].add(obj_id)

    def get_all_subindices_in_trie_node(self, trie_id):
        return self.__get_trie_node(trie_id)['subindices'].values()

    def get_all_key_value_pairs_in_trie_node(self, trie_id):
        return self.__get_trie_node(trie_id)['subindices'].items()

    def get_subindex_from_trie_by_key(self, trie_id, key_element):
        return self.__get_trie_node(trie_id)['subindices'].get(key_element)

    def store_trie_subindex_for_trie_node_and_key(self, trie_id, key_element, subindex_id):
        subindices = self.__get_trie_node(trie_id)['subindices']
        if key_element in subindices:
            raise Exception("You cannot change the subindex associated to a key")
        subindices[key_element] = subindex_id

    def store_obj(self, obj):
        obj_id = self.objects_by_value.get(obj)
        if obj_id is None:
            obj_id = self.next_id()
            self.objects_by_id[obj_id] = obj
            self.objects_by_value[obj] = obj_id

        return obj_id


class DummyIndexedSerializingLogicObjectStorage(LogicObjectStorage):

    def __init__(self):
        storage = NodeStorage()

        self._objects: AbstruseIndex = InMemSerializingAbstruseIndex(
            storage_id="root",
            storage=storage
        )

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
