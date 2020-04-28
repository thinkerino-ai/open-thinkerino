from __future__ import annotations

from typing import Iterable, Tuple, Optional

from aitools.logic import LogicObject
from aitools.storage.base import NodeStorage
from aitools.storage.index import TrieIndex, AbstruseIndex, AbstruseKeyElement


class NodeStoringAbstruseIndex(AbstruseIndex[LogicObject]):
    def __init__(self, *, storage_id, node_storage: NodeStorage):
        self.id = storage_id
        self.node_storage = node_storage
        self._subindex_tree = NodeStoringTrieIndex(
            storage_id=node_storage.get_subindex_id_for_abstruse_node(self.id),
            node_storage=node_storage
        )

    @property
    def subindex_tree(self):
        return self._subindex_tree

    def make_node(self):
        return NodeStoringAbstruseIndex(
            storage_id=self.node_storage.next_id(),
            node_storage=self.node_storage
        )

    def _get_all_objects(self) -> Iterable[T]:
        return (
            self.node_storage.get_object(_id)
            for _id in self.node_storage.get_all_object_ids_in_abstruse_node(self.id)
        )

    def _maybe_store_object(self, obj):
        obj_id = self.node_storage.store_obj(obj)
        self.node_storage.store_object_for_abstruse_node(self.id, obj_id)


class NodeStoringTrieIndex(TrieIndex[NodeStoringAbstruseIndex]):
    def __init__(self, *, storage_id, node_storage: NodeStorage):
        self.id = storage_id
        self.node_storage = node_storage

    def _maybe_store_object(self, obj: NodeStoringAbstruseIndex):
        self.node_storage.store_abstruse_node_for_trie_index_id(self.id, obj.id)

    def _get_or_create_subindex(self, key_element) -> TrieIndex:
        index_id = self.node_storage.get_subindex_from_trie_by_key(self.id, key_element)

        if index_id is None:
            index_id = self.node_storage.next_id()
            self.node_storage.store_trie_subindex_for_trie_node_and_key(self.id, key_element, index_id)

        return NodeStoringTrieIndex(
            storage_id=index_id,
            node_storage=self.node_storage
        )

    def make_node(self):
        return NodeStoringTrieIndex(
            storage_id=self.node_storage.next_id(),
            node_storage=self.node_storage
        )

    def _get_all_objects(self):
        return (
            NodeStoringAbstruseIndex(
                storage_id=obj_id,
                node_storage=self.node_storage
            )
            for obj_id in self.node_storage.get_all_object_ids_in_trie_node(self.id))

    def _get_all_subindices(self):
        return (
            NodeStoringTrieIndex(storage_id=index_id, node_storage=self.node_storage)
            for index_id in self.node_storage.get_all_subindices_in_trie_node(self.id)
        )

    def _get_all_keys_and_subindices(self) -> Iterable[Tuple[AbstruseKeyElement, TrieIndex]]:
        return (
            (key, NodeStoringTrieIndex(storage_id=index_id, node_storage=self.node_storage))
            for key, index_id in self.node_storage.get_all_key_value_pairs_in_trie_node(self.id)
        )

    def _get_subindex_by_key_element(self, key_element: AbstruseKeyElement) -> Optional[TrieIndex]:
        index_id = self.node_storage.get_subindex_from_trie_by_key(self.id, key_element)
        if index_id is None:
            return None
        return NodeStoringTrieIndex(storage_id=index_id, node_storage=self.node_storage)


