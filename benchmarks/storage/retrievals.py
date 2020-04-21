from aitools.logic import Variable
from aitools.storage.base import LogicObjectStorage


def retrieve_all_formulas(storage: LogicObjectStorage) -> int:
    total = sum(1 for _ in storage.search_unifiable(Variable()))
    return total