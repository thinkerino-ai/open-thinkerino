"""
Tests for aitools.utils.asynctools.multiplex

Implemented cases:
    completion
        processes the whole input, with various buffer_sizes

TODO cases:
    cancelled_on_get
    cancelled_on_yield
    cancelled_on_wait
    failing_input

TODO some coroutines are never awaited since I'm handling them manually,
  which leads to RuntimeWarning about it, I should include tests on this
"""
import asyncio
import unittest.mock

import pytest

from aitools.utils import asynctools


def create_mock_task():
    res = unittest.mock.MagicMock()
    res.done.return_value = False
    return res


def complete_mock_task(mock_task):
    mock_task.done.return_value = True


def _run_to_first_await(multiplexer):
    gen = multiplexer.asend(None)
    next(gen)
    return gen


def _get_and_validate_queue_and_pill(mock_create_task):
    queues = [
        call.args[0].cr_frame.f_locals['queue']
        for call in mock_create_task.call_args_list
    ]
    pills = [
        call.args[0].cr_frame.f_locals['poison_pill']
        for call in mock_create_task.call_args_list
    ]
    internal_queue = queues[0]
    poison_pill = pills[0]
    assert all(q is internal_queue for q in queues)
    assert all(p is poison_pill for p in pills)
    return internal_queue, poison_pill



@pytest.mark.parametrize(argnames='buffer_size', argvalues=[0, 1, 10])
@unittest.mock.patch('aitools.utils.asynctools.asyncio.create_task')
@unittest.mock.patch('aitools.utils.asynctools.asyncio.wait')
def test__completion(mock_wait, mock_create_task, buffer_size):
    source_count = 5
    result_count = 10
    mock_tasks = [create_mock_task() for _ in range(source_count)]

    mock_create_task.side_effect = mock_tasks

    sources = [asynctools.yield_forever(i) for i in range(source_count)]

    multiplexer = asynctools.multiplex(
        *sources,
        buffer_size=buffer_size
    )

    gen = _run_to_first_await(multiplexer)

    internal_queue, poison_pill = _get_and_validate_queue_and_pill(mock_create_task)

    # process some results
    for i in range(result_count):
        internal_queue.put_nowait(i)
        try:
            next(gen)
        except StopIteration as e:
            assert e.value == i
        gen = multiplexer.asend(None)

    # put and process poison pills to close the process
    for _ in range(source_count - 1):
        internal_queue.put_nowait(poison_pill)
        try:
            next(gen)
        except StopIteration as e:
            assert e.value is None

    # put the last pill by hand
    internal_queue.put_nowait(poison_pill)

    # all tasks are complete now
    for task in mock_tasks:
        complete_mock_task(task)

    # we have reached the end of the function
    with pytest.raises(StopAsyncIteration):
        next(gen)

    # no task was cancelled since they were all done
    for task in mock_tasks:
        task.cancel.not_called()

    mock_wait.assert_called_once_with(mock_tasks, return_when=asyncio.ALL_COMPLETED)
