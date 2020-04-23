from timeit import Timer

from benchmarks.storage.distributions import dummy_distribution
from benchmarks.storage.insertions import make_insert_n_formulas, leave_storage_empty
from benchmarks.storage.retrievals import retrieve_all_formulas
from tests.implementations import storage_implementations as test_storage_implementations

all_storage_implementations = test_storage_implementations
all_distributions = [dummy_distribution]
retrieval_initializers = [make_insert_n_formulas(10), make_insert_n_formulas(100), make_insert_n_formulas(1000),
                          make_insert_n_formulas(10000)]
all_initializers = [leave_storage_empty] + retrieval_initializers
all_insertions = [make_insert_n_formulas(10), make_insert_n_formulas(100), make_insert_n_formulas(1000),
                  make_insert_n_formulas(10000)]
all_retrievals = [retrieve_all_formulas]


def do_insertion_benchmarks(storage_implementations, initial_distributions, storage_initializers,
                            insertion_distributions, insertion_benchmarks):
    for initial_distribution in initial_distributions:
        for storage_initializer in storage_initializers:
            for insertion_distribution in insertion_distributions:
                for insertion_benchmark in insertion_benchmarks:
                    for storage_implementation_name, storage_implementation in storage_implementations.items():
                        storage = storage_implementation()
                        storage_initializer(storage, initial_distribution)

                        timer = Timer(stmt=lambda: insertion_benchmark(storage, insertion_distribution))

                        print(
                            "storage ", storage_implementation_name,
                            " initialized as ", storage_initializer.__name__,
                            " with initial distribution ", initial_distribution.__name__,
                            " doing benchmark ", insertion_benchmark.__name__,
                            " with distribution ", insertion_distribution.__name__,
                        )

                        reps, seconds = timer.autorange()

                        print(f"\t{seconds / reps} per iteration, total {seconds} ({reps} iterations)\n\n")


def do_retrieval_benchmarks(storage_implementations, initial_distributions, storage_initializers, retrieval_benchmarks):
    for initial_distribution in initial_distributions:
        for storage_initializer in storage_initializers:
            for retrieval_benchmark in retrieval_benchmarks:
                for storage_implementation_name, storage_implementation in storage_implementations.items():
                    storage = storage_implementation()
                    storage_initializer(storage, initial_distribution)

                    timer = Timer(stmt=lambda: retrieval_benchmark(storage))

                    print(
                        "storage ", storage_implementation_name,
                        " initialized as ", storage_initializer.__name__,
                        " with initial distribution ", initial_distribution.__name__,
                        " doing benchmark ", retrieval_benchmark.__name__,
                    )

                    reps, seconds = timer.autorange()

                    print(f"\t{seconds/reps} per iteration, total {seconds} ({reps} iterations)\n\n")


def do_automatic_benchmarks():
    print("***************************** INSERTIONS *****************************")
    do_insertion_benchmarks(
        storage_implementations=all_storage_implementations,
        initial_distributions=all_distributions,
        storage_initializers=all_initializers,
        insertion_distributions=all_distributions,
        insertion_benchmarks=all_insertions
    )
    print("***************************** RETRIEVALS *****************************")
    do_retrieval_benchmarks(
        storage_implementations=all_storage_implementations,
        initial_distributions=all_distributions,
        storage_initializers=retrieval_initializers,
        retrieval_benchmarks=all_retrievals
    )
    print("***************************** DONE *****************************")