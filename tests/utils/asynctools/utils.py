import asyncio
import collections

from aitools.utils import asynctools


async def _generate_integers(name: str, max_value: int):
    for i in range(max_value):
        yield name, i


async def _generate_many(*, buffer_size, **generators: int):
    _generators = {arg: _generate_integers(arg, val) for arg, val in generators.items()}

    async for res in asynctools.multiplex(*_generators.values(), buffer_size=buffer_size):
        yield res


class SomeException(Exception):
    pass


async def await_yield_and_log(n, *, log: list):
    try:
        for i in range(n):

            res = await asyncio.sleep(0, result=i)
            log.append(res)
            yield res
    except BaseException as e:
        log.append(e)
        raise e


async def yield_then_fail(result, n):
    for i in range(n):
        yield f"{result}-{i}"

    raise SomeException()


async def push_result_to_queue(res, queue, poison_pill):
    await asynctools.push_each_to_queue(asynctools.asynchronize([res]), queue=queue, poison_pill=poison_pill)


def step(coroutine):
    return coroutine.send(None)