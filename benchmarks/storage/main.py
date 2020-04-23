from datetime import datetime

from aitools.logic.utils import normalize_variables
from benchmarks.storage.auto import all_storage_implementations
from benchmarks.storage.distributions import dummy_distribution


def run_basic_benchmark():
    formulas = list(dummy_distribution(0))[:4000]
    print(len(formulas))

    for storage_implementation in all_storage_implementations:
        with storage_implementation() as storage:

            tstart = datetime.now()
            if storage.supports_transactions():
                print(f"storage (transactional):{storage_implementation.__name__}")
                with storage.transaction():
                    storage.add(*formulas)
            else:
                print(f"storage :{storage_implementation.__name__}")
                storage.add(*formulas)
            tadded = datetime.now()
            print(f"\t{tadded - tstart} to insert")
            count = 0
            for f in formulas:
                f = normalize_variables(f)
                for _ in storage.search_unifiable(f):
                    count += 1
            tend = datetime.now()
            print(f"\t{tend - tadded} to retrieve")
            print(count)
            print(len(storage))
            print("-----------------------------------------------------------------")


if __name__ == '__main__':
    run_basic_benchmark()