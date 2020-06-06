"""
Tests for aitools.utils.asynctools.multiplex

Implemented cases:
    completion
        processes the whole input, with various buffer_sizes
    cancelled_on_get
        processes some of the input, then cancels the process while it is waiting for the next result on the queue
        uses various buffer sizes
    cancelled_on_yield
        processes some of the input, then cancels the process right after it yielded a result
        uses various buffer sizes
    cancelled_on_wait
        processes all of the input, then cancels the process while it is waiting for task exit
        uses various buffer sizes

TODO cases:
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
    gen.send(None)
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
def test__cancelled_on_get(mock_wait, mock_create_task, buffer_size):
    source_count = 5
    result_count = 10
    mock_tasks = [create_mock_task() for _ in range(source_count)]

    mock_create_task.side_effect = mock_tasks

    sources = [asynctools.yield_forever(i) for i in range(source_count)]

    multiplexer = asynctools.multiplex(
        *sources,
        buffer_size=buffer_size # TODO make more cases or parametrize this
    )

    gen = _run_to_first_await(multiplexer)

    internal_queue, poison_pill = _get_and_validate_queue_and_pill(mock_create_task)

    # process some results
    for i in range(result_count):
        internal_queue.put_nowait(i)
        try:
            gen.send(None)
        except StopIteration as e:
            assert e.value == i
        gen = multiplexer.asend(None)

    # put and process some poison pills
    completed_tasks_count = source_count // 2
    for _ in range(completed_tasks_count):
        internal_queue.put_nowait(poison_pill)
        try:
            gen.send(None)
        except StopIteration as e:
            assert e.value is None

    # process some more results
    for i in range(result_count):
        internal_queue.put_nowait(i)
        try:
            gen.send(None)
        except StopIteration as e:
            assert e.value == i
        gen = multiplexer.asend(None)

    # some tasks were completed
    for task in mock_tasks[:completed_tasks_count]:
        complete_mock_task(task)

    # run it to then next await, then cancel it
    gen.send(None)
    with pytest.raises(asyncio.CancelledError):
        gen.throw(asyncio.CancelledError)

    # we have reached the end of the function
    with pytest.raises(StopAsyncIteration):
        gen = multiplexer.asend(None)
        gen.send(None)

    # completed tasks are not cancelled, all others are
    for task in mock_tasks[:completed_tasks_count]:
        task.cancel.assert_not_called()
    for task in mock_tasks[completed_tasks_count:]:
        task.cancel.assert_called_once()

    mock_wait.assert_called_once_with(mock_tasks, return_when=asyncio.ALL_COMPLETED)


@pytest.mark.parametrize(argnames='buffer_size', argvalues=[0, 1, 10])
@unittest.mock.patch('aitools.utils.asynctools.asyncio.create_task')
@unittest.mock.patch('aitools.utils.asynctools.asyncio.wait')
def test__cancelled_on_yield(mock_wait, mock_create_task, buffer_size):
    source_count = 5
    result_count = 10
    mock_tasks = [create_mock_task() for _ in range(source_count)]

    mock_create_task.side_effect = mock_tasks

    sources = [asynctools.yield_forever(i) for i in range(source_count)]

    multiplexer = asynctools.multiplex(
        *sources,
        buffer_size=buffer_size # TODO make more cases or parametrize this
    )

    gen = _run_to_first_await(multiplexer)

    internal_queue, poison_pill = _get_and_validate_queue_and_pill(mock_create_task)

    # process some results
    for i in range(result_count):
        internal_queue.put_nowait(i)
        try:
            gen.send(None)
        except StopIteration as e:
            assert e.value == i
        gen = multiplexer.asend(None)

    # put and process some poison pills
    completed_tasks_count = source_count // 2
    for _ in range(completed_tasks_count):
        internal_queue.put_nowait(poison_pill)
        try:
            gen.send(None)
        except StopIteration as e:
            assert e.value is None

    # process some more results
    for i in range(result_count):
        internal_queue.put_nowait(i)
        try:
            gen.send(None)
        except StopIteration as e:
            assert e.value == i
        gen = multiplexer.asend(None)

    # some tasks were completed
    for task in mock_tasks[:completed_tasks_count]:
        complete_mock_task(task)

    # cancel the generator at the current "yield"
    with pytest.raises(asyncio.CancelledError):
        gen.throw(asyncio.CancelledError)

    # we have reached the end of the function
    with pytest.raises(StopAsyncIteration):
        gen = multiplexer.asend(None)
        gen.send(None)

    # completed tasks are not cancelled, all others are
    for task in mock_tasks[:completed_tasks_count]:
        task.cancel.assert_not_called()
    for task in mock_tasks[completed_tasks_count:]:
        task.cancel.assert_called_once()

    mock_wait.assert_called_once_with(mock_tasks, return_when=asyncio.ALL_COMPLETED)


@pytest.mark.parametrize(argnames='buffer_size', argvalues=[0, 1, 10])
@unittest.mock.patch('aitools.utils.asynctools.asyncio.create_task')
def test__cancelled_on_wait(mock_create_task, buffer_size):
    mock_wait_calls = []

    async def mock_wait(tasks, return_when):
        mock_wait_calls.append(dict(tasks=tasks, return_when=return_when))
        await asynctools.noop()

    # I'm mocking like this since I couldn't find another way to make "multiplex" yield control
    #  on the "await asyncio.wait(...)", since AsyncMock yields directly with no wait
    with unittest.mock.patch('aitools.utils.asynctools.asyncio.wait', new=mock_wait):
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
                gen.send(None)
            except StopIteration as e:
                assert e.value == i
            gen = multiplexer.asend(None)

        # put and process some poison pills
        for _ in range(source_count // 2):
            internal_queue.put_nowait(poison_pill)
            try:
                gen.send(None)
            except StopIteration as e:
                assert e.value is None

        # process some more results
        for i in range(result_count):
            internal_queue.put_nowait(i)
            try:
                gen.send(None)
            except StopIteration as e:
                assert e.value == i
            gen = multiplexer.asend(None)

        # put and process the remaining poison pills
        for _ in range(source_count // 2):
            internal_queue.put_nowait(poison_pill)
            try:
                gen.send(None)
            except StopIteration as e:
                assert e.value is None

        # put the last pill by hand
        internal_queue.put_nowait(poison_pill)

        # all tasks are complete now
        for task in mock_tasks:
            complete_mock_task(task)

        # run until the last await
        gen.send(None)

        # cancel it
        gen.throw(asyncio.CancelledError)

        # since the wait is forced, we need to perform another step
        with pytest.raises(asyncio.CancelledError):
            gen.send(None)

        # we have reached the end of the function
        with pytest.raises(StopAsyncIteration):
            gen = multiplexer.asend(None)
            gen.send(None)

        # no task was cancelled since they were all done
        for task in mock_tasks:
            task.cancel.assert_not_called()

        # asyncio.wait was called once
        assert mock_wait_calls == [
            dict(tasks=mock_tasks, return_when=asyncio.ALL_COMPLETED),
            dict(tasks=mock_tasks, return_when=asyncio.ALL_COMPLETED),
        ]
