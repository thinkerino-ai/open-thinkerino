import asyncio
from threading import Thread

import typing

import janus


def is_inside_task():
    try:
        asyncio.current_task()
    except RuntimeError:
        return False
    else:
        return True


async def noop():
    await asyncio.sleep(0)


async def put_forever(element, queue: asyncio.Queue):
    while True:
        await queue.put(element)


async def yield_forever(val):
    while True:
        yield val


async def asynchronize(iterable: typing.Iterable):
    for element in iterable:
        yield element


async def wrap_item(item):
    yield item


async def process_with_loopback(input_sequence: typing.AsyncGenerator, processor):
    # TODO make buffer_size configurable
    queue = asyncio.Queue(maxsize=1)
    start_pill = object()
    poison_pill = object()

    task = asyncio.create_task(
        _process_all_inputs(input_sequence, processor, queue=queue,
                            start_pill=start_pill, poison_pill=poison_pill)
    )

    collection_process = _collect_results_with_loopback(loopback=processor, queue=queue, start_pill=start_pill,
                                                        poison_pill=poison_pill)
    try:
        try:
            async for res in collection_process:
                yield res

        finally:
            await collection_process.aclose()
    finally:
        if not task.done():
            task.cancel()
        await asyncio.wait([task], return_when=asyncio.ALL_COMPLETED)


# TODO I'm not satisfied with this name
async def _process_all_inputs(input_sequence: typing.AsyncGenerator, processor, *,
                              queue, start_pill, poison_pill):
    tasks = []
    try:
        await queue.put(start_pill)
        async for element in input_sequence:
            await queue.put(start_pill)
            tasks.append(asyncio.create_task(processor(element, queue=queue, poison_pill=poison_pill)))
        await queue.put(poison_pill)
        if len(tasks) > 0:
            await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
    except BaseException as e:
        for task in tasks:
            if not task.done():
                task.cancel()
        if isinstance(e, Exception):
            await queue.put(e)
        else:
            raise e
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await input_sequence.aclose()
        if len(tasks) > 0:
            await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)


async def _collect_results_with_loopback(loopback, queue: asyncio.Queue, start_pill, poison_pill):
    currently_running_count = 0

    further_tasks = []

    try:
        while True:
            element = await queue.get()
            if element is start_pill:
                currently_running_count += 1
            elif element is poison_pill:
                currently_running_count -= 1
                if currently_running_count == 0:
                    break
            elif isinstance(element, Exception):
                raise element
            else:
                # we fake a start pill
                currently_running_count += 1
                further_tasks.append(asyncio.create_task(loopback(element, queue=queue, poison_pill=poison_pill)))
                yield element
    finally:
        for task in further_tasks:
            if not task.done():
                task.cancel()
        if len(further_tasks) > 0:
            await asyncio.wait(further_tasks, return_when=asyncio.ALL_COMPLETED)


async def push_each_to_queue(async_generator: typing.AsyncGenerator, queue, poison_pill: object):
    """Pushes each element of an asynchronous iterable into a queue, finally appending a poison pill."""
    try:
        async for res in async_generator:
            await queue.put(res)
        await queue.put(poison_pill)
    except Exception as e:
        await queue.put(e)
    finally:
        await async_generator.aclose()


async def multiplex(*generators: typing.AsyncGenerator, buffer_size: int) -> typing.AsyncGenerator:
    """Multiplexes several asynchronous iterables into one"""
    queue = asyncio.Queue(maxsize=buffer_size)

    currently_running_count = len(generators)

    tasks = []

    pill = object()
    for generator in generators:
        tasks.append(asyncio.create_task(push_each_to_queue(generator, queue, pill)))

    try:
        while currently_running_count > 0:
            res = await queue.get()

            if isinstance(res, Exception):
                raise res
            elif res is pill:
                currently_running_count -= 1
            else:
                yield res
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()

        if len(tasks) > 0:
            try:
                await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
            except (asyncio.CancelledError, GeneratorExit):
                # force wait
                await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
                raise


class Scheduler:
    def __init__(self, *, debug=False):
        self.loop = asyncio.new_event_loop()
        self.loop.set_debug(debug)
        self.__thread = Thread(target=self.loop.run_forever, daemon=True)
        self.__thread.start()
        self.__poison_pill = object()

    def make_queue(self, buffer_size) -> janus.Queue:
        return asyncio.run_coroutine_threadsafe(self.__make_queue(buffer_size), self.loop).result()

    async def __make_queue(self, max_size):
        return janus.Queue(maxsize=max_size)

    async def __get_from_queue(self, queue: asyncio.Queue):
        return await queue.get()

    def all_tasks(self):
        return asyncio.all_tasks(self.loop)

    def run(self, coroutine: typing.Coroutine):
        return asyncio.run_coroutine_threadsafe(coroutine, self.loop).result()

    def schedule_generator(self, generator: typing.AsyncGenerator, *, buffer_size: int):
        dual_queue = self.make_queue(buffer_size)

        fut = asyncio.run_coroutine_threadsafe(
            coro=push_each_to_queue(generator, dual_queue.async_q, self.__poison_pill),
            loop=self.loop
        )

        queue = dual_queue.sync_q
        try:
            while True:
                el = queue.get()

                if isinstance(el, Exception):
                    raise el
                elif el is self.__poison_pill:
                    return
                yield el
        finally:
            if not fut.done():
                fut.cancel()
            asyncio.run_coroutine_threadsafe(_wait_for_future(fut, self.loop), loop=self.loop).result()


# TODO remove this or consolidate it
async def _wait_for_future(fut, loop):
    wrapped = asyncio.wrap_future(fut, loop=loop)
    await asyncio.wait([wrapped], return_when=asyncio.ALL_COMPLETED)
