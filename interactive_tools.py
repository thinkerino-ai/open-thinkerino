import sqlite3
import sys
from contextlib import contextmanager

from aitools.storage.implementations.serializing import PickleSerializingLogicObjectStorage
from aitools.storage.implementations.sqlite import SqliteNodeStorage
from pytests.implementations import _make_context_manager_from_factory_and_context_manager


def __make_sqlite_connection_context_manager(path):
    @contextmanager
    def sqlite_connection():
        connection = sqlite3.connect(path)
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()
    return sqlite_connection


@contextmanager
def make_sqlite3_knowledge_base(path):
    cm = _make_context_manager_from_factory_and_context_manager(
        PickleSerializingLogicObjectStorage,
        _make_context_manager_from_factory_and_context_manager(
            SqliteNodeStorage,
            __make_sqlite_connection_context_manager(path)
        )
    )
    with cm() as kb:
        yield kb


def start_ipython_session(path):
    import IPython
    from aitools.logic import Substitution
    from aitools.logic.core import Variable, Constant
    from aitools.logic.utils import constants, variables, expr, VariableSource, ConstantSource, normalize_variables
    from aitools.proofs.language import And, Or, Implies, CoImplies, Not
    with make_sqlite3_knowledge_base(path) as kb:
        IPython.embed()


if __name__ == "__main__":
    start_ipython_session(sys.argv[1])