import sqlite3

from sqlalchemy import create_engine

from aitools.storage.implementations.dummy import DummyLogicObjectStorage, DummyIndexedLogicObjectStorage, \
    DummyPickleSerializingLogicObjectStorage, DummyNodeStorage
from aitools.storage.implementations.serializing import PickleSerializingLogicObjectStorage
from aitools.storage.implementations.sqlalchemy import SQLAlchemyNodeStorage
from aitools.storage.implementations.sqlite import SqliteNodeStorage


def make_storage_factory(storage_factory_name, storage_factory, node_storage_name, node_storage):
    return f"{storage_factory_name}({node_storage_name})", lambda: storage_factory(storage=node_storage())


def _create_in_memory_sqlalchemy_engine():
    db_str = "sqlite:///:memory:"
    engine = create_engine(db_str)
    return engine


def _create_in_memory_sqlite3_connection():
    db_str = ":memory:"
    return sqlite3.connect(db_str)


simple_storage_implementations = [DummyLogicObjectStorage, DummyIndexedLogicObjectStorage,
                                  DummyPickleSerializingLogicObjectStorage]
node_storage_implementations = dict(
    DummyNodeStorage=DummyNodeStorage,
    SqliteNodeStorage__inmem=lambda: SqliteNodeStorage(_create_in_memory_sqlite3_connection()),
    SqlAlchemyNodeStorage__inmem=lambda: SQLAlchemyNodeStorage(_create_in_memory_sqlalchemy_engine()),
)
node_based_storages_implementations = [PickleSerializingLogicObjectStorage]

storage_implementations = {
    **{impl.__name__: impl for impl in simple_storage_implementations},
    **dict(
        make_storage_factory(storage_factory.__name__, storage_factory, node_storage_name, node_storage)
        for storage_factory in node_based_storages_implementations
        for node_storage_name, node_storage in node_storage_implementations.items()
    )
}