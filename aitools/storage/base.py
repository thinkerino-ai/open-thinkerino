from abc import ABC, abstractmethod
from typing import Iterable, Tuple

from aitools.logic import LogicObject, Substitution


class LogicObjectStorage(ABC):
    @abstractmethod
    def add(self, *objects: LogicObject):
        raise NotImplementedError()

    @abstractmethod
    def search_unifiable(self, other: LogicObject) -> Iterable[Tuple[LogicObject, Substitution]]:
        raise NotImplementedError()

    @abstractmethod
    def __len__(self):
        raise NotImplementedError()