from abc import ABC, abstractmethod

from aitools.logic import LogicObject


class LogicObjectStorage(ABC):
    @abstractmethod
    def add(self, *objects: LogicObject):
        raise NotImplementedError()

    @abstractmethod
    def search_unifiable(self, other: LogicObject):
        raise NotImplementedError()

    @abstractmethod
    def __len__(self):
        raise NotImplementedError()