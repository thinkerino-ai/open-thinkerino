from typing import Set

from aitools.logic import LogicObject, Substitution
from aitools.storage.base import LogicObjectStorage


class DummyLogicObjectStorage(LogicObjectStorage):
    def __init__(self):
        self._objects: Set[LogicObject] = set()

    def add(self, *objects: LogicObject):
        for obj in objects:
            self._objects.add(obj)

    def search_unifiable(self, other: LogicObject):
        for obj in self._objects:
            unifier = Substitution.unify(obj, other)
            if unifier is not None:
                yield obj

    def __len__(self):
        return len(self._objects)
