from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Iterable, Tuple

from aitools.logic import LogicObject, Substitution


class LogicObjectStorage(ABC):

    def supports_transactions(self):
        try:
            with self.transaction():
                return True
        except (TypeError, NotImplementedError):
            return False

    @abstractmethod
    @contextmanager
    def transaction(self):
        raise NotImplementedError()

    @abstractmethod
    def add(self, *objects: LogicObject):
        raise NotImplementedError()

    @abstractmethod
    def search_unifiable(self, other: LogicObject) -> Iterable[Tuple[LogicObject, Substitution]]:
        raise NotImplementedError()

    @abstractmethod
    def __len__(self):
        raise NotImplementedError()


class NodeStorage:

    @abstractmethod
    @contextmanager
    def transaction(self):
        raise NotImplementedError()

    @abstractmethod
    def next_id(self):
        pass

    @abstractmethod
    def store_abstruse_node_for_trie_index_id(self, trie_id, abstruse_id):
        pass

    @abstractmethod
    def get_all_object_ids_in_trie_node(self, trie_id):
        pass

    @abstractmethod
    def get_object(self, object_id):
        pass

    @abstractmethod
    def get_all_object_ids_in_abstruse_node(self, abstruse_id):
        pass

    @abstractmethod
    def get_subindex_id_for_abstruse_node(self, abstruse_id):
        pass

    @abstractmethod
    def store_object_for_abstruse_node(self, abstruse_id, object_id):
        pass

    @abstractmethod
    def get_all_subindices_in_trie_node(self, trie_id):
        pass

    @abstractmethod
    def get_all_key_value_pairs_in_trie_node(self, trie_id):
        pass

    @abstractmethod
    def get_subindex_from_trie_by_key(self, trie_id, key_element):
        pass

    @abstractmethod
    def store_trie_subindex_for_trie_node_and_key(self, trie_id, key_element, subindex_id):
        pass

    @abstractmethod
    def store_obj(self, obj):
        pass