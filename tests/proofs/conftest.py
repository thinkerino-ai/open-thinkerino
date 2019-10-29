import logging

import pytest

from aitools.proofs.knowledge_bases.dummy import DummyKnowledgeBase, DummyIndexedKnowledgeBase
from aitools.proofs.knowledge_bases.zodb import ZodbPersistentKnowledgeBase, IndexedZodbPersistenceKnowledgeBase

logging.basicConfig(format="[%(levelname)s] %(name)s - %(message)s")
logging.getLogger().setLevel(logging.NOTSET)
logging.getLogger('txn').setLevel(logging.WARN)


@pytest.fixture(params=[DummyKnowledgeBase, ZodbPersistentKnowledgeBase, DummyIndexedKnowledgeBase,
                        IndexedZodbPersistenceKnowledgeBase])
def TestKnowledgeBase(request):
    return request.param
