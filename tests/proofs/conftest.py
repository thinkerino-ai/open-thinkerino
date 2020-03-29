import logging

import pytest

from aitools.proofs.knowledge_bases.dummy import DummyKnowledgeBase, DummyIndexedKnowledgeBase
from aitools.proofs.knowledge_bases.redis import IndexedRedisPersistenceKnowledgeBase
from aitools.proofs.knowledge_bases.zodb import ZodbPersistentKnowledgeBase, IndexedZodbPersistenceKnowledgeBase

logging.basicConfig(format="[%(levelname)s] %(name)s - %(message)s")
logging.getLogger().setLevel(logging.NOTSET)
logging.getLogger('txn').setLevel(logging.WARN)


@pytest.fixture(params=[DummyKnowledgeBase, ZodbPersistentKnowledgeBase, DummyIndexedKnowledgeBase,
                        IndexedZodbPersistenceKnowledgeBase, IndexedRedisPersistenceKnowledgeBase])
def TestKnowledgeBase(request):
    # TODO actually remove this :P
    if request.param == IndexedRedisPersistenceKnowledgeBase:
        pytest.xfail("This will be removed shortly")
    return request.param
