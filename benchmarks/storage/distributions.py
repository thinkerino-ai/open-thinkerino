import random

from aitools.logic import Constant, Variable


def dummy_distribution(seed, constant_count, predicate_count, variable_count, max_child_length, repetitions,
                       total_depth):

    predicates_ = [Constant() for _ in range(predicate_count)]
    constants_ = [Constant() for _ in range(constant_count)]
    variables = [Variable() for _ in range(variable_count)]

    random.seed(seed)

    def _generate(max_child_length, repetitions, remaining_depth):
        if remaining_depth == 0:
            if len(constants_) > 0:
                yield from random.choices(constants_, k=repetitions * 2)
            if len(variables) > 0:
                yield from random.choices(variables, k=repetitions)
        else:
            prev = tuple(_generate(max_child_length, repetitions, remaining_depth - 1))

            yield from prev

            for length in range(1, max_child_length):
                for _ in range(repetitions):
                    yield random.choice(predicates_)(*random.choices(prev, k=length))

    yield from (x for x in _generate(max_child_length, repetitions, total_depth)
                if not isinstance(x, (Variable, Constant)))
