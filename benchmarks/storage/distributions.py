import random

from aitools.logic import Constant, Variable


def dummy_distribution(n):
    random.seed(n)
    base_size = 10
    constant_count = base_size * 10
    variable_count = base_size * 1
    constants_ = [Constant() for _ in range(constant_count)]
    variables = [Variable() for _ in range(variable_count)]

    def _generate(max_child_length, repetitions, remaining_depth):
        if remaining_depth == 0:
            yield from random.choices(constants_, k=repetitions * 2)
            yield from random.choices(variables, k=repetitions)
        else:
            prev = tuple(_generate(max_child_length, repetitions, remaining_depth - 1))

            yield from prev

            for length in range(1, max_child_length):
                for _ in range(repetitions):
                    yield random.choice(constants_)(*random.choices(prev, k=length))

    yield from (x for x in _generate(5, 100, 10) if not isinstance(x, (Variable, Constant)))
