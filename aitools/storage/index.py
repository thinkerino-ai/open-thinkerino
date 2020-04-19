from __future__ import annotations

import itertools
import logging
from abc import ABC, abstractmethod
from collections import deque
from typing import TypeVar, Generic, Dict, MutableSet, Iterable, Sequence, Protocol, Any, Tuple, Sized, Type, Union, \
    List, Optional

from aitools.logic import Expression, LogicObject, Variable

logger = logging.getLogger(__name__)
T = TypeVar('T')
WILDCARD = -1

AbstruseKeyElement = Optional[Union[int, T]]
AbstruseKeySlice = List[AbstruseKeyElement[T]]
AbstruseKey = List[AbstruseKeySlice[T]]


# TODO: typing gives issues with PyCharm :/
# TODO: make this lazy so that it is calculated when it is traversed (otherwise searching for very deep formulas in the
#  AbstruseIndex could be inefficient)
def make_key(formula: LogicObject) -> AbstruseKey[LogicObject]:
    res: AbstruseKey[LogicObject] = []

    def inner(_formula: LogicObject, level: int):
        if len(res) == level:
            res.append([])

        if isinstance(_formula, Expression):
            res[level].append(len(_formula.children))
            for child in _formula.children:
                inner(child, level + 1)
        elif isinstance(_formula, Variable):
            res[level].append(WILDCARD)
        else:
            res[level].append(_formula)

    inner(formula, 0)
    return res


class TrieIndex(Generic[T], ABC):
    def add(self, key, obj: T):
        logger.info("Adding key %s for object %s", key, obj)
        self._add(key, obj, level=0)

    def _add(self, key, obj, level: int):
        if level == len(key):
            self._maybe_store_object(obj)
        else:
            key_element = key[level]
            subindex = self._get_or_create_subindex(key_element)
            subindex._add(key, obj, level + 1)

    @abstractmethod
    def _maybe_store_object(self, obj: T):
        raise NotImplementedError()

    @abstractmethod
    def _get_or_create_subindex(self, key_element) -> TrieIndex:
        raise NotImplementedError()

    def retrieve(self, key, *, use_wildcard = True) -> Iterable[T]:
        logger.info("Retrieving key %s", key)
        for r in self._retrieve(key, level=0, use_wildcard=use_wildcard):
            yield r

    def _retrieve(self, key, *, level: int, use_wildcard: bool, found_key=None):
        found_key = found_key if found_key is not None else []
        if key is None:
            for obj in self._get_all_objects():
                yield obj, found_key
            for subindex in self._get_all_subindices():
                res = subindex._retrieve(key, level=level + 1, found_key=found_key, use_wildcard=use_wildcard)
                yield from res
        else:
            if level == len(key):
                logger.debug("key completely traversed, returning all objects")
                for obj in self._get_all_objects():
                    yield obj, found_key
            else:
                yield from self._traverse_next_key_element(key, level, found_key, use_wildcard)

    @abstractmethod
    def _get_all_objects(self):
        raise NotImplementedError()

    @abstractmethod
    def _get_all_subindices(self):
        raise NotImplementedError()

    def _traverse_next_key_element(self, key, level, found_key, use_wildcard):
        key_element = key[level]
        logger.debug("Considering the following element of the key: %s", key_element)
        if key_element != WILDCARD or not use_wildcard:
            logger.debug("Searching for key element explicitly")
            yield from self._search_for_key_element_explicitly(key, key_element, level, found_key, use_wildcard)
            if key_element != WILDCARD:
                logger.debug("Searching for variables in the index")
                yield from self._search_for_variable(key, level, found_key, use_wildcard)
        elif key_element == WILDCARD and use_wildcard:
            logger.debug("Element is a variable, performing wildcard search")
            yield from self._search_wildcard(key, level, found_key, use_wildcard)

    def _search_wildcard(self, key, level, found_key, use_wildcard):
        for subkey_element, subindex in self._get_all_keys_and_subindices():
            logger.debug("Matched %s, recursion...", subkey_element)
            res = list(subindex._retrieve(key, level=level + 1, found_key=found_key + [subkey_element],
                                          use_wildcard=use_wildcard))
            logger.debug("Recursion returned %s elements", len(res))
            for r in res:
                yield r

    @abstractmethod
    def _get_all_keys_and_subindices(self) -> Iterable[Tuple[AbstruseKeyElement, TrieIndex[T]]]:
        raise NotImplementedError()

    @abstractmethod
    def _get_subindex_by_key_element(self, key_element: AbstruseKeyElement) -> Optional[TrieIndex[T]]:
        raise NotImplementedError()

    def _search_for_variable(self, key, level, found_key, use_wildcard):
        if use_wildcard and (subindex := self._get_subindex_by_key_element(WILDCARD)) is not None:
                logger.debug("Subindex contains variable, recursion...")
                res = list(subindex._retrieve(key, level=level + 1, found_key=found_key + [WILDCARD],
                                              use_wildcard=use_wildcard))
                logger.debug("Recursion returned %s elements", len(res))
                for r in res:
                    yield r

    def _search_for_key_element_explicitly(self, key, key_element, level, found_key, use_wildcard):
        if (subindex := self._get_subindex_by_key_element(key_element)) is not None:
            logger.debug("Element is in the subindex, recursion...")
            res = list(subindex._retrieve(key, level=level + 1, found_key=found_key + [key_element],
                                          use_wildcard=use_wildcard))
            logger.debug("Recursion returned %s elements", len(res))
            for r in res:
                yield r


class AbstruseIndex(Generic[T], ABC):

    @property
    @abstractmethod
    def subindex_tree(self):
        raise NotImplementedError()

    def add(self, key, obj):
        self._add(key, obj, level=0)

    def _add(self, key, obj, *, level):
        _key = key[level] if level < len(key) else None
        if _key is None or len(_key) == 0:
            self._maybe_store_object(obj)
            return

        further_abstrusion: Sequence[AbstruseIndex] = tuple(self.subindex_tree.retrieve(_key, use_wildcard=False))

        if len(further_abstrusion) > 1:
            raise Exception("Do I even know what I'm doing?")

        if len(further_abstrusion) == 0:
            dest: AbstruseIndex = self.make_node()
            self.subindex_tree.add(_key, dest)
        else:
            dest, _ = further_abstrusion[0]

        dest._add(key, obj, level=level+1)

    @abstractmethod
    def make_node(self):
        raise NotImplementedError()

    def retrieve(self, key):
        return self._retrieve(full_key=key, level=0)

    def _retrieve(self, *, full_key, previous_key=None, projection_key=None, level):
        _key = full_key[level] if full_key and level < len(full_key) else None

        logger.info("Index is retrieving full key %s", _key)

        for obj in self._get_all_objects():
            yield obj

        # TODO probably can be removed by exploiting the projection :/ but I'm lazy and it's 3 am
        if _key is None:
            yield from self._full_search(full_key=full_key, previous_key=previous_key, level=level+1)
        else:
            if projection_key is not None:
                _key = self._project_key(previous_key=previous_key, projection_key=projection_key, current_key=_key)
                logger.debug("Projected key to %s", _key)

            if len(_key) > 0:
                logger.debug("Index looking for sources...")
                subindices = list(self.subindex_tree.retrieve(_key))
                logger.debug("Index found %s sources", len(subindices))

                for subindex, found_key in subindices:
                    res = list(subindex._retrieve(
                        full_key=full_key, previous_key=_key, projection_key=found_key, level=level+1
                    ))
                    for r in res:
                        logger.debug("Index has found result %s", r)
                        yield r

    @abstractmethod
    def _get_all_objects(self) -> Iterable[T]:
        raise NotImplementedError()

    @abstractmethod
    def _maybe_store_object(self, obj):
        raise NotImplementedError()

    def _full_search(self, *, full_key, previous_key, level):
        subindices: Iterable[AbstruseIndex] = list(self.subindex_tree.retrieve(None))
        for subindex, found_key in subindices:
            res = list(subindex._retrieve(
                full_key=full_key, previous_key=previous_key, projection_key=found_key,level=level+1
            ))
            for r in res:
                yield r

    @staticmethod
    def _project_key(*, previous_key, projection_key, current_key):
        current_key = deque(current_key)
        result = []

        for i, projector in enumerate(projection_key):
            if previous_key[i] == WILDCARD and isinstance(projector, int):
                # if previous_key[i] is a wildcard, the current key wouldn't have a corresponding item, so we "insert" wildcards
                result.extend(itertools.repeat(WILDCARD, projector))
            elif isinstance(projector, int):
                # we take the "n" elements from the current key
                for j in range(projector):
                    result.append(current_key.popleft())

        while len(current_key) > 0:
            result.append(current_key.popleft())

        return result
