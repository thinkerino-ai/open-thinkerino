import pickle
from typing import Dict

from aitools.logic import LogicObject, Expression, Variable
from aitools.storage.base import LogicObjectStorage
from aitools.utils.abstruse_index import WILDCARD


class InMemLogicObjectStorage(LogicObjectStorage):
    def __init__(self):
        self._objects: Dict[int, LogicObject] = {}

    def add(self, obj: LogicObject):
        self._objects[obj.id] = pickle.dumps(obj)

    def get_by_id(self, obj_id):
        return pickle.loads(self._objects[obj_id])

    def remove_by_id(self, obj_id):
        del self._objects[obj_id]


def make_plain_key(formula: LogicObject):
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
            res[level].append(str(hash(formula)))

    inner(formula, 0)
    return res


class InMemAbstruseIndexedStorage:
    def __init__(self):
        self.storage = InMemLogicObjectStorage

    def add(self, obj: LogicObject):
        """Adds obj to the storage and to the index"""
        pass

    def retrieve_unification_candidates(self, obj: LogicObject):
        """Retrieves all objects that could unify with obj"""
        pass