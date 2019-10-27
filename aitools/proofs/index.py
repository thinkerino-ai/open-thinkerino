import itertools
import logging
from collections import defaultdict, deque
from collections.abc import Iterable

from aitools.logic import Expression, LogicObject, Variable, Substitution

logger = logging.getLogger(__name__)

class _ListKeyIndex:
    def __init__(self):
        self.subindex = {}
        self.objects = set()

    def add(self, key, obj):
        logger.info(f"Adding key %s for object %s", key, obj)
        def inner(index: _ListKeyIndex, level: int):
            if level == len(key):
                index.objects.add(obj)
            else:
                key_element = key[level]
                if key_element not in index.subindex:
                    index.subindex[key_element] = _ListKeyIndex()
                inner(index.subindex[key_element], level + 1)

        inner(self, 0)

    def retrieve(self, key, use_wildcard = True):
        logger.info("Retrieving key %s", key)
        def inner(index: _ListKeyIndex, level: int, found_key=None):
            found_key = found_key[:] if found_key is not None else []
            if key is None:
                for obj in index.objects:
                    yield obj, found_key
                for sub in index.subindex.values():
                    res = list(inner(sub, level + 1, found_key))
                    for r in res:
                        yield r
            else:
                if level == len(key):
                    logger.debug(f"key completely traversed, returning {len(index.objects)} objects")
                    for obj in index.objects:
                        yield obj, found_key
                else:
                    key_element = key[level]
                    logger.debug("Considering the following element of the key: %s", key_element)
                    if key_element is not Variable or not use_wildcard:
                        logger.debug("Searching for key element explicitly")
                        if key_element in index.subindex:
                            logger.debug("Element is in the subindex, recursion...")
                            res = list(inner(index.subindex[key_element], level + 1, found_key=found_key + [key_element]))
                            logger.debug("Recursion returned %s elements", len(res))
                            for r in res:
                                yield r
                        logger.debug("Searching for variables corresponding to the element")
                        if key_element is not Variable and Variable in index.subindex and use_wildcard:
                            logger.debug("Variable is in the subindex, recursion...")
                            res = list(
                                inner(index.subindex[Variable], level + 1, found_key=found_key + [Variable]))
                            logger.debug("Recursion returned %s elements", len(res))
                            for r in res:
                                yield r
                    elif key_element is Variable and use_wildcard:
                        logger.debug("Performing a wildcard search...")
                        for subkey_element, subindex in index.subindex.items():
                            logger.debug("Matched %s, recursion...", subkey_element)
                            res = list(inner(subindex, level + 1, found_key + [subkey_element]))
                            logger.debug("Recursion returned %s elements", len(res))
                            for r in res:
                                yield r

        for r in inner(self, 0):
            yield r


class AbstruseIndex:
    def __init__(self, level=0):
        self.level = level
        self.subindex = _ListKeyIndex()
        self.objects = set()

    def add(self, formula: Expression):
        key = self.make_key(formula, self.level + 1)
        if key is None or len(key) == 0:
            self.objects.add(formula)
            return

        further_abstrusion = tuple(self.subindex.retrieve(key, use_wildcard=False))

        if len(further_abstrusion) > 1:
            raise Exception("Do I even know what I'm doing?")

        if len(further_abstrusion) == 0:
            dest: AbstruseIndex = AbstruseIndex(self.level + 1)
            self.subindex.add(key, dest)
        else:
            dest, _ = further_abstrusion[0]

        dest.add(formula)

    def retrieve(self, formula: Expression, previous_key=None, projection_key=None):
        key = self.make_key(formula, self.level + 1)
        logger.info("Index is retrieving %s and using key %s", formula, key)

        for obj in self.objects:
            yield obj

        # TODO probably can be removed by exploiting the projection :/ but I'm lazy and it's 3 am
        # do full search
        if key is None:
            sources = list(self.subindex.retrieve(None))
            for source, found_key in sources:
                res = list(source.retrieve(formula, previous_key=previous_key, projection_key=found_key))
                for r in res:
                    yield r
        else:
            if projection_key is not None:
                key = self.project_key(previous_key, projection_key, key)
                logger.debug("Projected key to %s", key)

            if len(key) > 0:
                logger.debug("Index looking for sources...")
                sources = list(self.subindex.retrieve(key))
                logger.debug("Index found %s sources", len(sources))

                for source, found_key in sources:
                    res = list(source.retrieve(formula, previous_key=key, projection_key=found_key))
                    for r in res:
                        logger.debug("Index has found result %s", r)
                        yield r

    @staticmethod
    def project_key(previous_key, projection_key, key):
        key = deque(key)
        result = []

        for i, projector in enumerate(projection_key):
            if previous_key[i] is Variable and isinstance(projector, int):
                result.extend(itertools.repeat(Variable, projector))
            elif isinstance(projector, int):
                for j in range(projector):
                    result.append(key.popleft())

        while len(key) > 0:
            result.append(key.popleft())

        return result

    @staticmethod
    def make_key(formula: LogicObject, depth: int):
        if depth == 0:
            if isinstance(formula, Expression):
                return len(formula.children)
            elif isinstance(formula, Variable):
                return Variable
            else:
                return formula
        else:
            if isinstance(formula, Expression):
                res = []
                for child in formula.children:
                    key = AbstruseIndex.make_key(child, depth - 1)
                    if isinstance(key, Iterable):
                        for k in key:
                            res.append(k)
                    elif key is not None:
                        res.append(key)
                return res
            else:
                return None