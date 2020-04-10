import logging

import pytest

from aitools.proofs.knowledge_bases.dummy import DummyKnowledgeBase, DummyIndexedKnowledgeBase
from aitools.proofs.knowledge_bases.redis import IndexedRedisPersistenceKnowledgeBase

logging.basicConfig(format="[%(levelname)s] %(name)s - %(message)s")
logging.getLogger().setLevel(logging.WARNING)
logging.getLogger('txn').setLevel(logging.WARNING)


@pytest.fixture(params=[DummyKnowledgeBase, DummyIndexedKnowledgeBase, IndexedRedisPersistenceKnowledgeBase])
def TestKnowledgeBase(request):
    # TODO actually remove this :P
    if request.param == IndexedRedisPersistenceKnowledgeBase:
        pytest.xfail("This will be removed shortly")
    return request.param
