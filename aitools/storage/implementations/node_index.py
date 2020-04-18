from __future__ import annotations

from typing import Iterable, Tuple

from aitools.logic import LogicObject
from aitools.storage.implementations.dummy import DummyNodeStorage
from aitools.storage.index import TrieIndex, AbstruseIndex, AbstruseKeyElement


class InMemSerializingAbstruseIndex(AbstruseIndex[LogicObject]):
    def __init__(self, *, storage_id, storage):
        self.id = storage_id
        self.storage: DummyNodeStorage = storage
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


