import pytest

from aitools.utils import asynctools
from pytests.utils.asynctools.utils import _generate_integers, _generate_many, SomeException, yield_then_fail, push_result_to_queue


@pytest.mark.parametrize('buffer_size', [0, 1, 2, 10])
def test_simple_generator_result(scheduler, buffer_size):
    res = list(
        scheduler.schedule_generator(
            _generate_integers('a', 3),
            buffer_size=0
        )
    )

    assert res == [('a', 0), ('a', 1), ('a', 2)]


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


@pytest.mark.parametrize('buffer_size', [0, 1, 2])
def test_tasks_are_cleared(scheduler, buffer_size):
    _ = list(scheduler.schedule_generator(_generate_integers('a', 3), buffer_size=buffer_size))

    # is this safe?
    assert scheduler.all_tasks() == set()


def test_schedule_generator_cancellation(scheduler):
    gen = scheduler.schedule_generator(_generate_integers('a', 1000), buffer_size=100)
    next(gen)

    assert len(scheduler.all_tasks()) > 0

    gen.close()

    assert scheduler.all_tasks() == set()


def test_multiplex_cancellation(scheduler):
    gen = scheduler.schedule_generator(
        asynctools.multiplex(
            asynctools.yield_forever('a'),
            asynctools.yield_forever('b'),
            buffer_size=1
        ),
        buffer_size=1
    )
    next(gen)

    assert len(scheduler.all_tasks()) > 0

    gen.close()

    assert scheduler.all_tasks() == set()


@pytest.mark.parametrize(argnames='inputs', argvalues=[['a_single_input'], range(100)])
def test_process_with_loopback(scheduler, inputs):
    gen = scheduler.schedule_generator(
        asynctools.process_with_loopback(
            asynctools.asynchronize(inputs),
            processor=lambda x, queue, poison_pill: asynctools.put_forever(x, queue)
        ),
        buffer_size=1
    )
    next(gen)

    assert len(scheduler.all_tasks()) > 0

    gen.close()

    assert scheduler.all_tasks() == set()


@pytest.mark.parametrize('n', [1, 2, 10])
def test_process_with_loopback_and_failing_input(scheduler, n):
    gen = scheduler.schedule_generator(
        asynctools.process_with_loopback(
            yield_then_fail('some_input', n),
            processor=push_result_to_queue
        ),
        buffer_size=1
    )
    with pytest.raises(SomeException):
        for _ in gen:
            pass

    assert scheduler.all_tasks() == set()


def test_all_other_functions():
    # TODO unit tests for process_with_loopback (and related functions)
    # TODO test that closing the scheduler shuts down everything properly, including the scheduler's thread
    # TODO test async APIs for kb.prove and kb.ponder
    # TODO ensure that it's hard to make mistakes, like... I don't know, sync/async tomfoolery
    pytest.xfail("Test many more cases")