from __future__ import annotations

import itertools
from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterable, Callable, List

from aitools.logic import Expression, Substitution, Variable, LogicObject, LogicWrapper
from aitools.proofs import context
from aitools.proofs.proof import Proof, Prover


class UnsafePonderException(Exception):
    pass


class PonderMode(Enum):
    KNOWN = auto()
    PROVE = auto()
    HYPOTHETICALLY = auto()


class HandlerArgumentMode(Enum):
    RAW = auto()
    MAP = auto()
    MAP_UNWRAPPED = auto()
    MAP_UNWRAPPED_REQUIRED = auto()
    MAP_UNWRAPPED_NO_VARIABLES = auto()
    MAP_NO_VARIABLES = auto()


class HandlerSafety(Enum):
    TOTALLY_UNSAFE = auto()
    SAFE_FOR_HYPOTHESES = auto()
    SAFE = auto()


class TriggeringFormula(Prover):
    def __call__(self, formula: Expression, _kb=None, _truth: bool = True,
                 _previous_substitution: Substitution = None) -> Iterable[Proof]:
        raise TypeError('This is a "fake" prover, don\'t try to use it')


@dataclass
class Pondering(Prover):
    listener: Listener
    triggering_formula: LogicObject

    def __call__(self, formula: Expression, _kb=None, _truth: bool = True,
                 _previous_substitution: Substitution = None) -> Iterable[Proof]:
        raise TypeError('This is a "fake" prover, don\'t try to use it')



class Listener:
    def __init__(self, *, handler: Callable, listened_formula: LogicObject, argument_mode: HandlerArgumentMode,
                 pure: bool, safety: HandlerSafety):
        self.handler = handler
        self.listened_formula = listened_formula
        self.argument_mode = argument_mode
        self.pure = pure
        self.safety = safety

        if handler.__code__.co_posonlyargcount > 0:
            # TODO allow also kw-only args
            raise ValueError("Handlers cannot have positional-only arguments")

        self._func_arg_names = handler.__code__.co_varnames

        if self.argument_mode == HandlerArgumentMode.RAW and self._func_arg_names != ('formula', 'substitution'):
            raise ValueError(f"{HandlerArgumentMode.RAW} requires the handler to take two arguments: "
                             f"(formula, substitution)")

    def ponder(self, formula: LogicObject) -> Iterable[Proof]:
        if context.is_hypothetical_scenario() and self.safety == HandlerSafety.TOTALLY_UNSAFE:
            raise UnsafePonderException("Unsafe listener cannot be used in hypothetical scenarios")

        unifier = Substitution.unify(formula, self.listened_formula)

        if unifier is None:
            return

        try:
            args_by_name = self._extract_args_by_name(formula, unifier)
        except ValueError:
            return

        result = self.handler(**args_by_name)

        if result is None:
            return

        # if the handler returned a single value, wrap it in an iterable
        if isinstance(result, (LogicObject, tuple)):
            result = (result,)

        for item in result:
            if isinstance(item, tuple):
                conclusion, premises = item
            else:
                conclusion = item
                premises = ()

            trigger_premise = Proof(
                inference_rule=TriggeringFormula(),
                conclusion=formula,
                substitution=Substitution()  # TODO remove this, I don't like it anymore
            )
            proof = Proof(
                inference_rule=Pondering(listener=self, triggering_formula=formula),
                conclusion=conclusion,
                substitution=Substitution(),  # TODO remove this, I don't like it anymore
                premises=tuple(itertools.chain((trigger_premise,), premises))
            )

            yield proof

    @staticmethod
    def _map_args(substitution: Substitution, func_arg_names: List[str]):

        bindings_by_variable_name = {}
        # TODO switch to some public API to get the bindings and maybe make this more efficient
        for var in substitution._bindings_by_variable:
            bound_object = substitution.get_bound_object_for(var)

            if bound_object:
                bindings_by_variable_name[var.name] = bound_object
        prepared_args = {}
        for arg in func_arg_names:
            if arg in bindings_by_variable_name:
                prepared_args[arg] = bindings_by_variable_name[arg]
        return prepared_args

    def _extract_args_by_name(self, formula: LogicObject, unifier: Substitution):
        if self.argument_mode == HandlerArgumentMode.RAW:
            args_by_name = dict(formula=formula, substitution=unifier)
        else:
            args_by_name = self._map_args(substitution=unifier, func_arg_names=self._func_arg_names)
            if self.argument_mode == HandlerArgumentMode.MAP:
                pass
            elif self.argument_mode == HandlerArgumentMode.MAP_NO_VARIABLES:
                if any(isinstance(arg, Variable) for arg in args_by_name.values()):
                    raise ValueError()
            elif self.argument_mode == HandlerArgumentMode.MAP_UNWRAPPED:
                args_by_name = {
                    key: arg.value if isinstance(arg, LogicWrapper) else arg
                    for key, arg in args_by_name.items()
                }
            elif self.argument_mode == HandlerArgumentMode.MAP_UNWRAPPED_REQUIRED:
                if any(not isinstance(arg, LogicWrapper) for arg in args_by_name.values()):
                    raise ValueError()

                args_by_name = {
                    key: arg.value if isinstance(arg, LogicWrapper) else arg
                    for key, arg in args_by_name.items()
                }
            elif self.argument_mode == HandlerArgumentMode.MAP_UNWRAPPED_NO_VARIABLES:
                if any(isinstance(arg, Variable) for arg in args_by_name.values()):
                    raise ValueError()

                args_by_name = {
                    key: arg.value if isinstance(arg, LogicWrapper) else arg
                    for key, arg in args_by_name.items()
                }
            else:
                raise NotImplementedError(f"Unsupported argument mode: {self.argument_mode}")

        return args_by_name
