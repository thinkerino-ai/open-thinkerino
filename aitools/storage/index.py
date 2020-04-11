from __future__ import annotations

import itertools
import logging
from abc import ABC, abstractmethod
from collections import deque
from typing import TypeVar, Generic, Dict, MutableSet, Iterable, Sequence

from aitools.logic import Expression, LogicObject, Variable


# TODO: typing
# TODO: make this lazy so that it is calculated when it is traversed (otherwise searching for very deep formulas in the
#  AbstruseIndex could be inefficient)
def make_key(formula: LogicObject):
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
            res[level].append(formula)

    inner(formula, 0)
    return res


logger = logging.getLogger(__name__)
T = TypeVar('T')
WILDCARD = None


class TrieIndex(Generic[T], ABC):
    def __init__(self, *, subindex_container: Dict, object_container: MutableSet):
        self.subindices = subindex_container
        self.objects = object_container

    def add(self, key, obj: T):
        logger.info(f"Adding key %s for object %s", key, obj)
        self._add(key, obj, level=0)

    def _add(self, key, obj, level: int):
        if level == len(key):
            if obj not in self.objects:
                self.objects.add(obj)
        else:
            key_element = key[level]
            if key_element not in self.subindices:
                self.subindices[key_element] = self.make_node()
            subindex: TrieIndex = self.subindices[key_element]
            subindex._add(key, obj, level + 1)

    @abstractmethod
    def make_node(self):
        raise NotImplementedError()

    def retrieve(self, key, *, use_wildcard = True) -> Iterable[T]:
        logger.info("Retrieving key %s", key)
        for r in self._retrieve(key, level=0, use_wildcard=use_wildcard):
            yield r

    def _retrieve(self, key, *, level: int, use_wildcard: bool, found_key=None):
        found_key = found_key if found_key is not None else []
        if key is None:
            for obj in self.objects:
                yield obj, found_key
            for subindex in self.subindices.values():
                res = list(subindex._retrieve(key, level=level + 1, found_key=found_key, use_wildcard=use_wildcard))
                yield from res
        else:
            if level == len(key):
                logger.debug(f"key completely traversed, returning {len(self.objects)} objects")
                for obj in self.objects:
                    yield obj, found_key
            else:
                yield from self._traverse_next_key_element(key, level, found_key, use_wildcard)

    def _traverse_next_key_element(self, key, level, found_key, use_wildcard):
        key_element = key[level]
        logger.debug("Considering the following element of the key: %s", key_element)
        if key_element is not WILDCARD or not use_wildcard:
            logger.debug("Searching for key element explicitly")
            yield from self._search_for_key_element_explicitly(key, key_element, level, found_key, use_wildcard)
            if key_element is not WILDCARD:
                logger.debug("Searching for variables in the index")
                yield from self._search_for_variable(key, level, found_key, use_wildcard)
        elif key_element is WILDCARD and use_wildcard:
            logger.debug("Element is a variable, performing wildcard search")
            yield from self._search_wildcard(key, level, found_key, use_wildcard)

    def _search_wildcard(self, key, level, found_key, use_wildcard):
        for subkey_element, subindex in self.subindices.items():
            logger.debug("Matched %s, recursion...", subkey_element)
            res = list(subindex._retrieve(key, level=level + 1, found_key=found_key + [subkey_element],
                                          use_wildcard=use_wildcard))
            logger.debug("Recursion returned %s elements", len(res))
            for r in res:
                yield r

    def _search_for_variable(self, key, level, found_key, use_wildcard):
        if WILDCARD in self.subindices and use_wildcard:
            logger.debug("Subindex contains variable, recursion...")
            subindex = self.subindices[WILDCARD]
            res = list(subindex._retrieve(key, level=level + 1, found_key=found_key + [WILDCARD],
                                          use_wildcard=use_wildcard))
            logger.debug("Recursion returned %s elements", len(res))
            for r in res:
                yield r

    def _search_for_key_element_explicitly(self, key, key_element, level, found_key, use_wildcard):
        if key_element in self.subindices:
            logger.debug("Element is in the subindex, recursion...")
            subindex = self.subindices[key_element]
            res = list(subindex._retrieve(key, level=level + 1, found_key=found_key + [key_element],
                                          use_wildcard=use_wildcard))
            logger.debug("Recursion returned %s elements", len(res))
            for r in res:
                yield r


class AbstruseIndex(ABC):
    def __init__(self, *, level=0, subindex: TrieIndex, object_container: MutableSet):
        self.level = level
        self.objects = object_container
        self._subindex_tree: TrieIndex[AbstruseIndex] = subindex

    @property
    def subindex_tree(self):
        return self._subindex_tree

    def add(self, key, obj):
        self._add(key, obj)

    def _add(self, key, obj):
        _key = key[self.level] if self.level < len(key) else None
        if _key is None or len(_key) == 0:
            if obj not in self.objects:
                self.objects.add(obj)
            return

        further_abstrusion: Sequence[AbstruseIndex] = tuple(self.subindex_tree.retrieve(_key, use_wildcard=False))

        if len(further_abstrusion) > 1:
            raise Exception("Do I even know what I'm doing?")

        if len(further_abstrusion) == 0:
            dest: AbstruseIndex = self.make_node(new_level=self.level + 1)
            self.subindex_tree.add(_key, dest)
        else:
            dest, _ = further_abstrusion[0]

        dest._add(key, obj)

    @abstractmethod
    def make_node(self, *, new_level):
        raise NotImplementedError()

    def retrieve(self, key):
        return self._retrieve(full_key=key)

    def _retrieve(self, *, full_key, previous_key=None, projection_key=None):
        _key = full_key[self.level] if full_key and self.level < len(full_key) else None

        logger.info("Index is retrieving full key %s", _key)

        for obj in self.objects:
            yield obj

        # TODO probably can be removed by exploiting the projection :/ but I'm lazy and it's 3 am
        if _key is None:
            yield from self._full_search(full_key=full_key, previous_key=previous_key)
        else:
            if projection_key is not None:
                _key = self._project_key(previous_key=previous_key, projection_key=projection_key, current_key=_key)
                logger.debug("Projected key to %s", _key)

            if len(_key) > 0:
                logger.debug("Index looking for sources...")
                subindices = list(self.subindex_tree.retrieve(_key))
                logger.debug("Index found %s sources", len(subindices))

                for subindex, found_key in subindices:
                    res = list(subindex._retrieve(full_key=full_key, previous_key=_key, projection_key=found_key))
                    for r in res:
                        logger.debug("Index has found result %s", r)
                        yield r

    def _full_search(self, *, full_key, previous_key):
        subindices: Iterable[AbstruseIndex] = list(self.subindex_tree.retrieve(None))
        for subindex, found_key in subindices:
            res = list(subindex._retrieve(full_key=full_key, previous_key=previous_key, projection_key=found_key))
            for r in res:
                yield r

    @staticmethod
    def _project_key(*, previous_key, projection_key, current_key):
        current_key = deque(current_key)
        result = []

        for i, projector in enumerate(projection_key):
            if previous_key[i] is WILDCARD and isinstance(projector, int):
                # if previous_key[i] is a wildcard, the current key wouldn't have a corresponding item, so we "insert" wildcards
                result.extend(itertools.repeat(WILDCARD, projector))
            elif isinstance(projector, int):
                # we take the "n" elements from the current key
                for j in range(projector):
                    result.append(current_key.popleft())

        while len(current_key) > 0:
            result.append(current_key.popleft())

        return result
