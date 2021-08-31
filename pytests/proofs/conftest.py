import logging

import pytest

from aitools.proofs.knowledge_base import KnowledgeBase
from pytests.implementations import storage_implementations

logging.basicConfig(format="[%(levelname)s] %(name)s - %(message)s")
logging.getLogger().setLevel(logging.WARNING)


@pytest.fixture(params=storage_implementations)
def test_knowledge_base(request):
    with request.param() as storage:
        kb = KnowledgeBase(storage)
        kb._scheduler.loop.set_debug(True)
        yield kb
