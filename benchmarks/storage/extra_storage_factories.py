import sqlite3
from tempfile import mkstemp

from aitools.storage.implementations.sqlite import SqliteNodeStorage


def sqlite_node_storage__file():
    # TODO close and delete the damn file, man :P
    _, filename = mkstemp(suffix=".db")
    return lambda: SqliteNodeStorage(sqlite3.connect(filename))