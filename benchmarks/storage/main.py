import statistics
from contextlib import contextmanager
from datetime import datetime

from aitools.logic.utils import normalize_variables
from benchmarks.storage.distributions import dummy_distribution
from tests.implementations import storage_implementations


@contextmanager
def dummy_context_manager():
    yield


def run_messy_benchmark(storage_implementations):
    formulas = list(
        dummy_distribution(
            seed=0, constant_count=500, predicate_count=25, variable_count=10, max_child_length=5, repetitions=100,
            total_depth=10
        )
    )[:4000]
    run_basic_benchmark(storage_implementations, formulas)


def run_small_benchmark(storage_implementations):
    formulas = list(
        dummy_distribution(
            seed=0, constant_count=500, predicate_count=25, variable_count=0, max_child_length=5, repetitions=1000,
            total_depth=3
        )
    )[:4000]
    run_basic_benchmark(storage_implementations, formulas)


def run_basic_benchmark(storage_implementations, formulas):
    print(f"{len(formulas)} formulas ({len(set(formulas))} distinct) "
          f"with an average size of {statistics.mean(f.size for f in formulas)}")
    for storage_implementation in storage_implementations:
        with storage_implementation() as storage:
            transaction_manager = storage.transaction if storage.supports_transactions() else dummy_context_manager
            # TODO understand how to prevent cache discarding ._. that seems to be the issue
            #  transaction_manager = dummy_context_manager
            tstart = datetime.now()

            print(f"storage :{storage_implementation.__name__}")
            with transaction_manager():
                normalized_formulas = (normalize_variables(f) for f in formulas)
                storage.add(*[res for res, _ in normalized_formulas])

            tadded = datetime.now()
            print(f"\t{tadded - tstart} to insert")
            results = []
            with transaction_manager():
                for f in formulas:
                    f, _ = normalize_variables(f)
                    for res_f, _ in storage.search_unifiable(f):
                        results.append(res_f)
            tend = datetime.now()
            print(f"\t{tend - tadded} to retrieve")
            print(len(results))
            print(len(set(results)))
            print("-----------------------------------------------------------------")


if __name__ == '__main__':
    implementations = storage_implementations[2:-1]
    run_small_benchmark(implementations)
    run_messy_benchmark(implementations)
