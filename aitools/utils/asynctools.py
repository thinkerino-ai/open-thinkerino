import asyncio
from asyncio import QueueEmpty
from threading import Thread

import typing


def is_inside_task():
    try:
        asyncio.current_task()
    except RuntimeError:
        return False
    else:
        return True


async def asynchronize(iterable: typing.Iterable):
    for element in iterable:
        yield element


async def wrap_item(item):
    yield item


async def process_with_loopback(inputs: typing.AsyncIterable, processor):
    # TODO make buffer_size configurable
    queue = asyncio.Queue(maxsize=1)
    start_pill = object()
    poison_pill = object()

    asyncio.create_task(
        __preprocess_pondering_inputs(inputs, processor, queue=queue,
                                      start_pill=start_pill, poison_pill=poison_pill)
    )

    async for res in __collect_results_with_loopback(loopback=processor, queue=queue,
                                                     start_pill=start_pill, poison_pill=poison_pill):
        yield res


async def __preprocess_pondering_inputs(inputs: typing.AsyncIterable, processor, *,
                                        queue, start_pill, poison_pill):
    await queue.put(start_pill)
    try:

        # TODO maybe here I could even gather them so that this task terminates when all of them do
        async for proof in inputs:
            await queue.put(start_pill)
            asyncio.create_task(processor(proof, queue=queue, poison_pill=poison_pill))
    finally:
        await queue.put(poison_pill)


async def __collect_results_with_loopback(loopback, queue: asyncio.Queue, start_pill, poison_pill):
    currently_running_count = 0

    while True:
        element = await queue.get()
        if element is start_pill:
            currently_running_count += 1
        elif element is poison_pill:
            currently_running_count -= 1
            if currently_running_count == 0:
                break
        else:
            # we fake a start pill
            currently_running_count += 1
            asyncio.create_task(loopback(element, queue=queue, poison_pill=poison_pill))
            yield element


async def push_each_to_queue(async_generator: typing.AsyncIterable, queue: asyncio.Queue, poison_pill: object):
    """Pushes each element of an asynchronous iterable into a queue, finally appending a poison pill."""
    try:
        async for res in async_generator:
            await queue.put(res)

    finally:
        await queue.put(poison_pill)


async def multiplex(*generators: typing.AsyncIterable, buffer_size: int) -> typing.AsyncIterable:
    """Multiplexes several asynchronous iterables into one"""
    queue = asyncio.Queue(maxsize=buffer_size)

    currently_running_count = len(generators)

    pill = object()
    for generator in generators:
        asyncio.create_task(push_each_to_queue(generator, queue, pill))

    while currently_running_count > 0:
        res = await queue.get()
        if res is pill:
            currently_running_count -= 1
        else:
            yield res


class ThreadSafeishQueue(asyncio.Queue):
    """A partially thread-safe version of an asyncio.Queue.

    It should be safe as long as only one thread writes and only one thread reads.
    """
    # TODO this is the quickest fix I could find but I'm pretty sure it's not actually safe :P
    def __init__(self, *, max_size, loop):
        super().__init__(maxsize=max_size)
        self.loop = loop

    async def __set_result_for_future(self, fut, res):
        await fut.set_result(res)

    def _wakeup_next(self, waiters):
        # TODO yeah I mean, the original was right below a comment stating "End of the overridable methods" :P
        #  what could go wrong?
        # Wake up the next waiter (if any) that isn't cancelled.
        while waiters:
            waiter = waiters.popleft()
            if not waiter.done():
                asyncio.run_coroutine_threadsafe(self.__set_result_for_future(waiter, None), loop=self.loop)
                break


class Scheduler:
    def __init__(self, *, debug=False):
        self.loop = asyncio.new_event_loop()
        self.loop.set_debug(debug)
        self.__thread = Thread(target=self.loop.run_forever, daemon=True)
        self.__thread.start()
        self.__poison_pill = object()

    def make_queue(self, buffer_size):
        return asyncio.run_coroutine_threadsafe(self.__make_queue(buffer_size), self.loop).result()

    async def __make_queue(self, max_size):
        return ThreadSafeishQueue(max_size=max_size, loop=self.loop)

    async def __get_from_queue(self, queue: asyncio.Queue):
        return await queue.get()

    def run(self, coroutine):
        return asyncio.run_coroutine_threadsafe(coroutine, self.loop).result()

    def schedule_generator(self, generator: typing.AsyncIterable, *, buffer_size: int):
        queue = self.make_queue(buffer_size)

        asyncio.run_coroutine_threadsafe(push_each_to_queue(generator, queue, self.__poison_pill), self.loop)

        while True:
            try:
                el = asyncio.run_coroutine_threadsafe(self.__get_from_queue(queue), self.loop).result()

                while True:
                    if el is self.__poison_pill:
                        return
                    yield el

                    el = queue.get_nowait()
            except QueueEmpty:
                pass

    def run_coroutine_threadsafe(self, coroutine):
        return asyncio.run_coroutine_threadsafe(coroutine, loop=self.loop)