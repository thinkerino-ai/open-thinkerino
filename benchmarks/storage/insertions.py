from typing import Callable, Iterable

from aitools.logic import LogicObject
from aitools.storage.base import LogicObjectStorage

def leave_storage_empty(
        storage: LogicObjectStorage,
        initial_distribution: Callable[[], Iterable[LogicObject]]
) -> LogicObjectStorage:
    return storage

def make_insert_n_formulas(n):
    def insert_n_formulas(storage: LogicObjectStorage, distribution: Callable[[], Iterable[LogicObject]]):
        for _, formula in zip(range(n), distribution()):
            storage.add(formula)

    insert_n_formulas.__name__ = f"insert_{n}_formulas"
    return insert_n_formulas
