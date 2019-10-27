import logging

import pytest

from aitools.proofs.knowledge_bases.dummy import DummyKnowledgeBase, DummyIndexedKnowledgeBase
from aitools.proofs.knowledge_bases.zodb import ZodbPersistentKnowledgeBase

logging.basicConfig(format="[%(levelname)s] %(name)s - %(message)s")
logging.getLogger().setLevel(logging.WARNING)


@pytest.fixture(params=[DummyKnowledgeBase, ZodbPersistentKnowledgeBase, DummyIndexedKnowledgeBase])
def TestKnowledgeBase(request):
    return request.param
