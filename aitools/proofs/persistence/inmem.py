import pickle
from typing import Dict

from aitools.logic import LogicObject
from aitools.proofs.persistence.base import LogicObjectStorage


class InMemLogicObjectStorage(LogicObjectStorage):
    def __init__(self):
        self._objects: Dict[int, LogicObject] = {}

    def add(self, obj: LogicObject):
        self._objects[obj.id] = pickle.dumps(obj)

    def get_by_id(self, obj_id):
        return pickle.loads(self._objects[obj_id])

    def remove_by_id(self, obj_id):
        del self._objects[obj_id]

