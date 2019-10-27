import pytest

from aitools.proofs.knowledge_bases.dummy import DummyKnowledgeBase, DummyIndexedKnowledgeBase
from aitools.proofs.knowledge_bases.zodb import ZodbPersistentKnowledgeBase


@pytest.fixture(params=[DummyKnowledgeBase, ZodbPersistentKnowledgeBase, DummyIndexedKnowledgeBase])
def TestKnowledgeBase(request):
    return request.param
