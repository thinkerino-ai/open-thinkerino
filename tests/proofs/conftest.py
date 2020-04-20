import logging

import pytest

from aitools.proofs.knowledge_base import KnowledgeBase
from tests.implementations import storage_implementations

logging.basicConfig(format="[%(levelname)s] %(name)s - %(message)s")
logging.getLogger().setLevel(logging.WARNING)


@pytest.fixture(params=storage_implementations)
def TestKnowledgeBase(request):
    return lambda: KnowledgeBase(request.param())
