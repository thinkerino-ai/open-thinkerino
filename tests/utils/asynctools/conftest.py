import pytest

from aitools.utils import asynctools


@pytest.fixture
def scheduler():
    return asynctools.Scheduler(debug=True)
