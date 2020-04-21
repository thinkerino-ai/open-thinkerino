import sqlite3

from sqlalchemy import create_engine

from aitools.storage.implementations.dummy import DummyLogicObjectStorage, DummyIndexedLogicObjectStorage, \
    DummyPickleSerializingLogicObjectStorage, DummyNodeStorage
from aitools.storage.implementations.serializing import PickleSerializingLogicObjectStorage
from aitools.storage.implementations.sqlalchemy import SQLAlchemyNodeStorage
from aitools.storage.implementations.sqlite import SqliteNodeStorage


def _make_storage_factory(storage, node_storage):
    return lambda: storage(storage=node_storage())


def _create_in_memory_sqlalchemy_engine():
    db_str = "sqlite:///:memory:"
    engine = create_engine(db_str)
    return engine


def _create_in_memory_sqlite3_connection():
    db_str = ":memory:"
    return sqlite3.connect(db_str)


simple_storage_implementations = [DummyLogicObjectStorage, DummyIndexedLogicObjectStorage,
                                  DummyPickleSerializingLogicObjectStorage]
node_storage_implementations = [
    DummyNodeStorage,
    lambda: SQLAlchemyNodeStorage(_create_in_memory_sqlalchemy_engine()),
    lambda: SqliteNodeStorage(_create_in_memory_sqlite3_connection()),
]
node_based_storages_implementations = [PickleSerializingLogicObjectStorage]

storage_implementations = [
    *simple_storage_implementations,
    *[
        _make_storage_factory(storage, node_storage)
        for storage in node_based_storages_implementations
        for node_storage in node_storage_implementations
    ]
]