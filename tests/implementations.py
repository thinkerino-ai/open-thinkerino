import sqlite3
import tempfile
from contextlib import contextmanager

from sqlalchemy import create_engine

from aitools.storage.implementations.dummy import DummyLogicObjectStorage, DummyIndexedLogicObjectStorage, \
    DummyPickleSerializingLogicObjectStorage, DummyNodeStorage
from aitools.storage.implementations.serializing import PickleSerializingLogicObjectStorage
from aitools.storage.implementations.sqlalchemy import SQLAlchemyNodeStorage
from aitools.storage.implementations.sqlite import SqliteNodeStorage


def make_storage_factory(storage_factory_name, storage_factory, node_storage_name, node_storage):
    return f"{storage_factory_name}({node_storage_name})", lambda: storage_factory(storage=node_storage())


@contextmanager
def in_memory_sqlalchemy_engine():
    db_str = "sqlite:///:memory:"
    engine = create_engine(db_str)
    connection = engine.connect()
    try:
        yield connection
    finally:
        connection.close()


@contextmanager
def in_memory_sqlite3_connection():
    db_str = ":memory:"
    connection = sqlite3.connect(db_str)
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


@contextmanager
def tempfile_sqlite_connection():
    with tempfile.NamedTemporaryFile(suffix=".db", prefix="sqlite") as db_file:
        connection = sqlite3.connect(db_file.name)
        connection.execute("PRAGMA cache_size=-200000")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()


def _make_context_manager_from_simple_factory(storage_factory: type):
    @contextmanager
    def inner():
        yield storage_factory()
    inner.__name__ = storage_factory.__name__
    return inner


def _make_context_manager_from_factory_and_context_manager(storage_factory: type, context_manager):
    @contextmanager
    def inner():
        with context_manager() as context:
            yield storage_factory(context)
    inner.__name__ = "{}({})".format(
        storage_factory.__name__,
        context_manager.__name__
    )
    return inner


simple_storage_implementations = [
    _make_context_manager_from_simple_factory(DummyLogicObjectStorage),
    _make_context_manager_from_simple_factory(
        DummyPickleSerializingLogicObjectStorage
    ),
    _make_context_manager_from_simple_factory(DummyIndexedLogicObjectStorage),
]

node_storage_implementations = [
    _make_context_manager_from_simple_factory(DummyNodeStorage),
    _make_context_manager_from_factory_and_context_manager(
        SqliteNodeStorage,
        in_memory_sqlite3_connection
    ),
    _make_context_manager_from_factory_and_context_manager(
        SqliteNodeStorage,
        tempfile_sqlite_connection
    ),
    _make_context_manager_from_factory_and_context_manager(
        SQLAlchemyNodeStorage,
        in_memory_sqlalchemy_engine
    ),
]
node_based_storages_implementations = [
    PickleSerializingLogicObjectStorage,
]

storage_implementations = [
    *simple_storage_implementations,
    *[
        _make_context_manager_from_factory_and_context_manager(
            storage_impl,
            node_storage_impl
        )
        for storage_impl in node_based_storages_implementations
        for node_storage_impl in node_storage_implementations
     ]
]