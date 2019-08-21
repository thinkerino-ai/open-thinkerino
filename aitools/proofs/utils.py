from functools import wraps
from typing import Union, Optional, Any, Iterable, Tuple

from aitools.logic import Substitution, Expression
from aitools.logic.utils import expr
from aitools.proofs.context import context
from aitools.proofs.proof import Proof, ProofSet, Prover


class EmbeddedProver(Prover):
    def __init__(self, prover_function):
        self.prover_function = prover_function

    def __call__(self, formula: Expression, _kb=None, _truth: bool = True) -> Iterable[Proof]:
        # TODO use _kb somehow :P I'm too tired to understand how/if/why/boop, probably via context?
        return self.normalize_results(formula=formula,
                                      requested_truth=_truth,
                                      raw_result=self.prover_function(*formula.children[1:]))

    def normalize_results(
            self,
            formula,
            requested_truth: bool,
            raw_result: Optional[Union[bool, Substitution, Tuple[bool, Substitution], Proof,
                                       Iterable[bool], Iterable[Substitution],
                                       Iterable[Tuple[bool, Substitution]], Iterable[Proof]]]) -> Iterable[Proof]:
        def _inner(res) -> Optional[Proof]:
            if res is None:
                # the prover returned None, so it couldn't prove neither true nor false
                return None
            elif isinstance(res, bool):
                if requested_truth == res:
                    return Proof(inference_rule=self, conclusion=formula, substitution=Substitution())
                else:
                    return None
            elif isinstance(res, Substitution):
                raise NotImplementedError
            elif (isinstance(raw_result, tuple) and len(raw_result) == 2 and
                  isinstance(raw_result[0], bool) and isinstance(raw_result[1], Substitution)):
                raise NotImplementedError
            elif isinstance(res, Proof):
                raise NotImplementedError
            else:
                # TODO other cases, not that the ones above are anywhere near implemented :$
                raise TypeError

        if (isinstance(raw_result, tuple) and len(raw_result) == 2 and
                isinstance(raw_result[0], bool) and isinstance(raw_result[1], Substitution) or
                not isinstance(raw_result, Iterable)):
            res = _inner(raw_result)
            if res is not None:
                yield res
        else:
            processed = (_inner(r) for r in raw_result)
            yield from (p for p in processed if p is not None)


# TODO this name is now terrible for completely different reasons
def predicateThatMakesAutoProvingFunctions(func=None, *args, predicate_source=None, variable_source=None):
    got_args = len(args) > 0 or predicate_source is not None or variable_source is not None

    def _decorate(prover_function):
        _predicate_source = predicate_source or context.predicate_source
        _variable_source = variable_source or context.variable_source

        predicate = getattr(_predicate_source, prover_function.__code__.co_name)

        # variables come from the **positional** arguments of `prover_function`
        arg_names = prover_function.__code__.co_varnames[:prover_function.__code__.co_argcount]
        formula = (predicate, *(getattr(_variable_source, arg_name) for arg_name in arg_names)) >> expr

        # TODO if called without arguments, it returns the predicate (hint: instead of a function use a class inheriting from predicate?)
        @wraps(prover_function)
        def _magic_wrapper(*_args): #TODO allow kwargs, everybody likes kwargs!
            if len(_args) != len(arg_names):
                raise TypeError("Wrong argument count for {}".format(prover_function))

            result = (predicate, *_args) >> expr

            result._embedded_prover = EmbeddedProver(prover_function)
            # TODO add __bool__ function to this expression
            # TODO add __iter__ function to this expression
            return result
            # naive_results: Any = prover_function(*_args)
            # normalized_results: Iterable[Proof] = normalize_results(_truth, naive_results)
            # return ProofSet(normalized_results)

        _magic_wrapper.formula = formula

        return _magic_wrapper

    if got_args and func is None:
        def _decorator(f):
            return _decorate(f)

        return _decorator
    elif not got_args and func is not None:
        return _decorate(func)
    else:
        raise ValueError("You cannot pass both func and args")
