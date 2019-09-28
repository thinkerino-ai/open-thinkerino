import pytest

from aitools.proofs.knowledge_bases.dummy import DummyKnowledgeBase
from aitools.proofs.knowledge_bases.zodb import ZodbPersistentKnowledgeBase


@pytest.fixture(params=[DummyKnowledgeBase, ZodbPersistentKnowledgeBase])
def test_kb_class(request):
    return request.param
