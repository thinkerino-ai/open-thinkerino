import asyncio
from typing import Tuple, AsyncIterable

import pytest

from aitools.utils import asynctools


async def _generate_integers(name: str, max_value: int) -> AsyncIterable[Tuple[str, int]]:
    for i in range(max_value):
        yield name, i


async def _generate_many(*, buffer_size, **generators: int) -> AsyncIterable[Tuple[str, int]]:
    _generators = {arg: _generate_integers(arg, val) for arg, val in generators.items()}

    async for res in asynctools.multiplex(*_generators.values(), buffer_size=buffer_size):
        yield res


@pytest.fixture
def scheduler():
    return asynctools.Scheduler(debug=True)


@pytest.mark.parametrize('buffer_size', [0, 1, 2, 10])
def test_simple_generator_result(scheduler, buffer_size):
    res = list(
        scheduler.schedule_generator(
            _generate_integers('a', 3),
            buffer_size=0
        )
    )

    assert res == [('a', 0), ('a', 1), ('a', 2)]


def test_tasks_are_cleared(scheduler):
    _ = list(scheduler.schedule_generator(_generate_integers('a', 3), buffer_size=0))

    # is this safe?
    assert len(asyncio.all_tasks(scheduler.loop)) == 0


@pytest.mark.parametrize(['mux_buffer_size', 'expected_result'], [
    (0, [('a', 0), ('a', 1), ('a', 2), ('b', 0), ('b', 1), ('b', 2)]),
    # TODO is the following deterministic? is it a valid assertion?
    (1, [('a', 0), ('a', 1), ('b', 0), ('a', 2), ('b', 1), ('b', 2)]),
])
def test_multiplexing(scheduler, mux_buffer_size, expected_result):
    res = list(
        scheduler.schedule_generator(
            _generate_many(
                buffer_size=mux_buffer_size,
                a=3,
                b=3
            ),
            buffer_size=0
        )
    )

    assert res == expected_result
