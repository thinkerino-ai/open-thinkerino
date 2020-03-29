from abc import ABC, abstractmethod

from aitools.logic import LogicObject


class LogicObjectStorage(ABC):
    @abstractmethod
    def add(self, obj: LogicObject):
        raise NotImplementedError()

    @abstractmethod
    def get_by_id(self, obj_id):
        raise NotImplementedError()

    @abstractmethod
    def remove_by_id(self, obj_id):
        raise NotImplementedError()
