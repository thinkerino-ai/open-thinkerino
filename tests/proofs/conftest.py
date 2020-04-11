import logging

import pytest

from aitools.proofs.knowledge_base import KnowledgeBase
from aitools.storage.dummy import DummyLogicObjectStorage, DummyIndexedLogicObjectStorage
from aitools.storage.inmem_serializing import InMemSerializingLogicObjectStorage, \
    DummyIndexedSerializingLogicObjectStorage

logging.basicConfig(format="[%(levelname)s] %(name)s - %(message)s")
logging.getLogger().setLevel(logging.WARNING)
logging.getLogger('txn').setLevel(logging.WARNING)


@pytest.fixture(params=[DummyLogicObjectStorage, DummyIndexedLogicObjectStorage, InMemSerializingLogicObjectStorage,
                        DummyIndexedSerializingLogicObjectStorage])
def TestKnowledgeBase(request):
    return lambda: KnowledgeBase(request.param())
