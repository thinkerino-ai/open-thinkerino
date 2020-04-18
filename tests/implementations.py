from aitools.storage.implementations.dummy import DummyLogicObjectStorage, DummyIndexedLogicObjectStorage, \
    DummyPickleSerializingLogicObjectStorage, DummyNodeStorage
from aitools.storage.implementations.serializing import PickleSerializingLogicObjectStorage

simple_storage_implementations = [DummyLogicObjectStorage, DummyIndexedLogicObjectStorage,
                                  DummyPickleSerializingLogicObjectStorage]
node_storage_implementations = [DummyNodeStorage]
node_based_storages_implementations = [PickleSerializingLogicObjectStorage]
storage_implementations = [
    *simple_storage_implementations,
    *[
        lambda: storage(storage=node_storage())
        for storage in node_based_storages_implementations
        for node_storage in node_storage_implementations
    ]
]