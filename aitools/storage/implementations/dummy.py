import pickle
from abc import abstractmethod
from contextlib import contextmanager
from typing import Set, Iterable, Tuple, Dict, Optional

from aitools.logic import LogicObject, Substitution
from aitools.storage.base import LogicObjectStorage, NodeStorage
from aitools.storage.index import make_key, TrieIndex, AbstruseIndex, AbstruseKey, AbstruseKeyElement, WILDCARD


class DummyLogicObjectStorage(LogicObjectStorage):
    def __init__(self):
        self._objects: Set[LogicObject] = set()

    @contextmanager
    def transaction(self):
        raise TypeError("Not supported, soriiii")

    def commit(self):
        raise TypeError("Not supported, soriiii")

    def rollback(self):
        raise TypeError("Not supported, soriiii")

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

    def _get_or_create_subindex(self, key_element) -> TrieIndex:
        if key_element not in self.subindices:
            self.subindices[key_element] = DummyTrieIndex()
        subindex: TrieIndex = self.subindices[key_element]
        return subindex

    def _get_all_subindices(self):
        return self.subindices.values()

    def _get_all_keys_and_subindices(self):
        return self.subindices.items()

    def _get_subindex_by_key_element(self, key_element: AbstruseKeyElement) -> Optional[TrieIndex]:
        return self.subindices.get(key_element)

    def _maybe_store_object(self, obj):
        if obj not in self.objects:
            self.objects.add(obj)

    def _get_all_objects(self):
        return iter(self.objects)


class DummyAbstruseIndex(AbstruseIndex):

    def __init__(self):
        self.objects = set()
        self._subindex_tree = DummyTrieIndex()

    def make_node(self):
        return DummyAbstruseIndex()

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

    @contextmanager
    def transaction(self):
        raise TypeError("Not supported, soriiii")

    def commit(self):
        raise TypeError("Not supported, soriiii")

    def rollback(self):
        raise TypeError("Not supported, soriiii")

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
        return sum(1 for _ in self._objects.retrieve([[WILDCARD]]))


class DummyPickleSerializingLogicObjectStorage(LogicObjectStorage):
    def __init__(self):
        self._objects: Set[bytes] = set()

    @contextmanager
    def transaction(self):
        raise TypeError("Not supported, soriiii")

    def commit(self):
        raise TypeError("Not supported, soriiii")

    def rollback(self):
        raise TypeError("Not supported, soriiii")

    def commit(self):
        raise TypeError("Not supported, soriiii")

    def rollback(self):
        raise TypeError("Not supported, soriiii")

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


class DummyNodeStorage(NodeStorage):

    def __init__(self):
        self.last_id = 0
        self.abstruse_nodes = {}
        self.trie_nodes = {}
        self.objects_by_id = {}
        self.objects_by_value = {}

    @contextmanager
    def transaction(self):
        # TODO: feeling lazy, might implement later :P
        raise NotImplementedError()

    def commit(self):
        # TODO: feeling lazy, might implement later :P
        raise NotImplementedError()

    def rollback(self):
        # TODO: feeling lazy, might implement later :P
        raise NotImplementedError()

    def next_id(self):
        self.last_id += 1
        return self.last_id

    def store_abstruse_node_for_trie_index_id(self, trie_id, abstruse_id):
        objects = self._get_trie_node(trie_id)['objects']
        objects.add(abstruse_id)

    def get_all_object_ids_in_trie_node(self, id):
        for obj_id in self._get_trie_node(id)['objects']:
            yield obj_id

    def _get_trie_node(self, trie_id):
        res = self.trie_nodes.get(trie_id)
        if res is None:
            res = dict(objects=set(), subindices={})
            self.trie_nodes[trie_id] = res

        return res

    def _get_abstruse_node(self, id):
        res = self.abstruse_nodes.get(id)
        if res is None:
            res = dict(objects=set(), subindex_id=self.next_id())
            self.abstruse_nodes[id] = res

        return res

    def get_object(self, id):
        return self.objects_by_id[id]

    def get_all_object_ids_in_abstruse_node(self, id):
        for obj_id in self._get_abstruse_node(id)['objects']:
            yield obj_id

    def get_subindex_id_for_abstruse_node(self, id):
        return self._get_abstruse_node(id)['subindex_id']

    def store_object_for_abstruse_node(self, id, obj_id):
        self._get_abstruse_node(id)['objects'].add(obj_id)

    def get_all_subindices_in_trie_node(self, trie_id):
        return self._get_trie_node(trie_id)['subindices'].values()

    def get_all_key_value_pairs_in_trie_node(self, trie_id):
        return self._get_trie_node(trie_id)['subindices'].items()

    def get_subindex_from_trie_by_key(self, trie_id, key_element):
        return self._get_trie_node(trie_id)['subindices'].get(key_element)

    def store_trie_subindex_for_trie_node_and_key(self, trie_id, key_element, subindex_id):
        subindices = self._get_trie_node(trie_id)['subindices']
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
