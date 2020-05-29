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


async def noop():
    pass


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


async def process_with_loopback(input_sequence: typing.AsyncIterable, processor):
    # TODO make buffer_size configurable
    queue = asyncio.Queue(maxsize=1)
    start_pill = object()
    poison_pill = object()

    task = asyncio.create_task(
        __process_all_inputs(input_sequence, processor, queue=queue,
                             start_pill=start_pill, poison_pill=poison_pill)
    )

    try:

        async for res in __collect_results_with_loopback(loopback=processor, queue=queue,
                                                         start_pill=start_pill, poison_pill=poison_pill):
            yield res
        # TODO experimental
        await task
    except (Exception, GeneratorExit):
        task.cancel()
        raise
    # else:
    #     await task


# TODO I'm not satisfied with this name
async def __process_all_inputs(input_sequence: typing.AsyncIterable, processor, *,
                               queue, start_pill, poison_pill):
    tasks = []
    try:
        await queue.put(start_pill)
        async for element in input_sequence:
            await queue.put(start_pill)
            tasks.append(asyncio.create_task(processor(element, queue=queue, poison_pill=poison_pill)))
        await queue.put(poison_pill)
        # TODO experimental
        await asyncio.gather(*tasks)
    except (Exception, asyncio.CancelledError) as e:
        for task in tasks:
            task.cancel()
        if isinstance(e, asyncio.CancelledError):
            raise e
        await queue.put(e)
        # TODO is this right? T_T I'm too sleepy T_T
        raise e
    # else:
    #     await asyncio.gather(*tasks)


async def __collect_results_with_loopback(loopback, queue: asyncio.Queue, start_pill, poison_pill):
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
        # TODO experimental
        await asyncio.gather(*further_tasks)
    except GeneratorExit:
        for task in further_tasks:
            task.cancel()
        raise


async def push_each_to_queue(async_generator: typing.AsyncIterable, queue: asyncio.Queue, poison_pill: object):
    """Pushes each element of an asynchronous iterable into a queue, finally appending a poison pill."""
    try:
        async for res in async_generator:
            await queue.put(res)
    except Exception as e:
        await queue.put(e)
        # TODO is this right? T_T I'm too sleepy T_T
        raise e
    else:
        await queue.put(poison_pill)


async def multiplex(*generators: typing.AsyncIterable, buffer_size: int) -> typing.AsyncIterable:
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
                for task in tasks:
                    task.cancel()
                raise res
            elif res is pill:
                currently_running_count -= 1
            else:
                yield res
        # TODO experimental
        await asyncio.gather(*tasks)
    except GeneratorExit:
        for task in tasks:
            task.cancel()
        raise


class ThreadSafeishQueue(asyncio.Queue):
    """A partially thread-safe version of an asyncio.Queue.

    It should be safe as long as only one thread writes and only one thread reads.
    """
    # TODO this is the quickest fix I could find but I'm pretty sure it's not actually safe :P
    def __init__(self, *, max_size, loop):
        super().__init__(maxsize=max_size)
        self.loop = loop

    async def __set_result_for_future(self, fut: asyncio.Future, res):
        if not fut.cancelled():
            fut.set_result(res)

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

    def all_tasks(self):
        return asyncio.all_tasks(self.loop)

    def run(self, coroutine: typing.Coroutine):
        return asyncio.run_coroutine_threadsafe(coroutine, self.loop).result()

    def schedule_generator(self, generator: typing.AsyncIterable, *, buffer_size: int):
        queue = self.make_queue(buffer_size)

        fut = asyncio.run_coroutine_threadsafe(push_each_to_queue(generator, queue, self.__poison_pill), self.loop)
        try:
            while True:
                try:
                    el = asyncio.run_coroutine_threadsafe(self.__get_from_queue(queue), self.loop).result()

                    while True:
                        if isinstance(el, Exception):
                            fut.cancel()
                            raise el
                        elif el is self.__poison_pill:
                            return
                        yield el

                        el = queue.get_nowait()
                except QueueEmpty:
                    pass
                except GeneratorExit:
                    fut.cancel()
                    raise
        finally:
            # TODO synchronize?
            pass