"""
Tests for aitools.utils.asynctools.push_each_to_queue

Implemented cases:
    completion__limited_queue
        processes the whole input, with a queue of max_size=1
    completion__unlimited_queue
        processes the whole input, with an unlimited queue
    failing_input__limited_queue
        the input raises an exception which is pushed as a result, with a queue of max_size=1
    failing_input__unlimited_queue
        the input raises an exception which is pushed as a result, with an unlimited queue
    cancelled_during_body__limited_queue
        the coroutine is cancelled during its own 'await', with a queue of max_size=1
    cancelled_while_in_subroutine__limited_queue
        the coroutine is cancelled while in a subroutine, with a queue of max_size=1
    cancelled_while_in_subroutine__unlimited_queue
        the coroutine is cancelled while in a subroutine, with an unlimited queue

NOTE: there is no cancelled_during_body__unlimited_queue, since it doesn't yield control during queue.put
"""
import asyncio

import pytest

from aitools.utils import asynctools
from pytests.utils.asynctools.utils import yield_then_fail, SomeException, step, await_yield_and_log


def test__completion__limited_queue():
    iterations = 10
    source = asynctools.asynchronize(range(iterations))
    poison_pill = object()
    queue = asyncio.Queue(maxsize=1)
    coro = asynctools.push_each_to_queue(source, queue=queue, poison_pill=poison_pill)

    step(coro)
    with pytest.raises(StopIteration):
        for i in range(iterations):
            assert queue.get_nowait() == i
            step(coro)

    assert queue.get_nowait() is poison_pill

    with pytest.raises(asyncio.QueueEmpty):
        queue.get_nowait()


def test__completion__unlimited_queue():
    iterations = 10
    source = asynctools.asynchronize(range(iterations))
    poison_pill = object()
    queue = asyncio.Queue(maxsize=0)
    coro = asynctools.push_each_to_queue(source, queue=queue, poison_pill=poison_pill)

    with pytest.raises(StopIteration):
        step(coro)

    for i in range(iterations):
        assert queue.get_nowait() == i

    assert queue.get_nowait() is poison_pill

    with pytest.raises(asyncio.QueueEmpty):
        queue.get_nowait()


def test__failing_input__limited_queue():
    iterations = 10
    source = yield_then_fail('some_result', iterations)
    poison_pill = object()
    queue = asyncio.Queue(maxsize=1)
    coro = asynctools.push_each_to_queue(source, queue=queue, poison_pill=poison_pill)

    step(coro)
    with pytest.raises(StopIteration):
        for i in range(iterations):
            assert queue.get_nowait() == f"some_result-{i}"
            step(coro)

    assert isinstance(queue.get_nowait(), SomeException)

    with pytest.raises(asyncio.QueueEmpty):
        queue.get_nowait()


def test__failing_input__unlimited_queue():
    iterations = 10
    source = yield_then_fail('some_result', iterations)
    poison_pill = object()
    queue = asyncio.Queue(maxsize=0)
    coro = asynctools.push_each_to_queue(source, queue=queue, poison_pill=poison_pill)

    with pytest.raises(StopIteration):
        step(coro)

    for i in range(iterations):
        assert queue.get_nowait() == f"some_result-{i}"

    assert isinstance(queue.get_nowait(), SomeException)

    with pytest.raises(asyncio.QueueEmpty):
        queue.get_nowait()


def test__cancelled_during_body__limited_queue():
    log = []
    iterations = 10
    source = await_yield_and_log(iterations, log=log)
    poison_pill = object()
    queue = asyncio.Queue(maxsize=1)
    coro = asynctools.push_each_to_queue(source, queue=queue, poison_pill=poison_pill)

    for i in range(iterations - 3):
        step(coro)
        step(coro)
        assert queue.get_nowait() == i

    assert log == list(range(iterations - 2))

    with pytest.raises(asyncio.CancelledError):
        coro.throw(asyncio.CancelledError)

    assert len(log) == iterations - 1
    assert isinstance(log[-1], GeneratorExit)

    with pytest.raises(asyncio.QueueEmpty):
        queue.get_nowait()


def test__cancelled_while_in_subroutine__limited_queue():
    log = []
    iterations = 10
    source = await_yield_and_log(iterations, log=log)
    poison_pill = object()
    queue = asyncio.Queue(maxsize=1)
    coro = asynctools.push_each_to_queue(source, queue=queue, poison_pill=poison_pill)

    for i in range(iterations - 3):
        step(coro)
        step(coro)
        assert queue.get_nowait() == i

    assert log == list(range(iterations - 2))

    step(coro)
    assert queue.get_nowait() == iterations - 3
    assert log == list(range(iterations - 2))

    with pytest.raises(asyncio.CancelledError):
        coro.throw(asyncio.CancelledError)

    assert len(log) == iterations - 1
    assert isinstance(log[-1], asyncio.CancelledError)

    with pytest.raises(asyncio.QueueEmpty):
        queue.get_nowait()


def test__cancelled_while_in_subroutine__unlimited_queue():
    log = []
    iterations = 10
    source = await_yield_and_log(iterations, log=log)
    poison_pill = object()
    queue = asyncio.Queue(maxsize=0)
    coro = asynctools.push_each_to_queue(source, queue=queue, poison_pill=poison_pill)

    step(coro)

    for i in range(iterations - 3):
        step(coro)
        assert queue.get_nowait() == i

    assert log == list(range(iterations - 3))

    with pytest.raises(asyncio.CancelledError):
        coro.throw(asyncio.CancelledError)

    assert len(log) == iterations - 2
    assert isinstance(log[-1], asyncio.CancelledError)

    with pytest.raises(asyncio.QueueEmpty):
        queue.get_nowait()
