from __future__ import annotations

import itertools
from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterable, Callable, List, Optional, Collection, Union

from aitools.logic import Expression, Substitution, Variable, LogicObject, LogicWrapper
from aitools.logic.utils import map_variables_by_name
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
class FormulaSubstitution:
    formula: LogicObject
    substitution: Substitution


@dataclass
class FormulaSubstitutionPremises:
    formula: LogicObject
    substitution: Substitution
    premises: Union[Proof, Collection[Proof]]


@dataclass
class Pondering(Prover):
    listener: Listener
    triggering_formula: LogicObject

    def __call__(self, formula: Expression, _kb=None, _truth: bool = True,
                 _previous_substitution: Substitution = None) -> Iterable[Proof]:
        raise TypeError('This is a "fake" prover, don\'t try to use it')


class Listener:
    def __init__(self, *,
                 listened_formula: LogicObject, handler: Callable,
                 argument_mode: HandlerArgumentMode, pass_substitution_as=...,
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

        if self.argument_mode == HandlerArgumentMode.RAW:
            if pass_substitution_as is None:
                raise ValueError(f"A substitution MUST be passed with {HandlerArgumentMode.RAW}")
            elif pass_substitution_as is Ellipsis:
                pass_substitution_as = 'substitution'

        else:
            if pass_substitution_as is Ellipsis:
                pass_substitution_as = None

        if isinstance(pass_substitution_as, str) and not pass_substitution_as.isidentifier():
            raise ValueError("When 'pass_substitution_as' is a string it must be a valid python identifier")

        self.pass_substitution_as: Optional[str] = pass_substitution_as

        self.variables_by_name = map_variables_by_name(listened_formula)
        if self.argument_mode != HandlerArgumentMode.RAW:
            unlistened_arg_names = list(
                arg_name
                for arg_name in self._func_arg_names
                if arg_name not in self.variables_by_name and arg_name != pass_substitution_as
            )
            if any(unlistened_arg_names):
                raise ValueError(f"Handler arguments {unlistened_arg_names} "
                                 f"are not present in formula {self.listened_formula}")

    def ponder(self, proof: Proof) -> Iterable[Proof]:
        formula = proof.conclusion
        if context.is_hypothetical_scenario() and self.safety == HandlerSafety.TOTALLY_UNSAFE:
            raise UnsafePonderException("Unsafe listener cannot be used in hypothetical scenarios")

        unifier = Substitution.unify(formula, self.listened_formula, previous=proof.substitution)

        if unifier is None:
            return

        try:
            args_by_name = self._extract_args_by_name(formula, unifier)
        except ValueError:
            return

        result = self.handler(**args_by_name)

        if result is None:
            return

        # if the handler returned a single value, wrap it in a tuple to make it iterable
        if (
                isinstance(result, (LogicObject, FormulaSubstitution, FormulaSubstitutionPremises)) or
                # the result is a pair or a triple, but not "made of results
                (
                        isinstance(result, tuple) and
                        len(result) in (2, 3) and
                        not all(isinstance(x, LogicObject) for x in result)
                )
        ):
            result = (result,)

        for item in result:
            if isinstance(item, tuple):
                if len(item) == 2:
                    conclusion, substitution = item
                    premises = ()
                elif len(item) == 3:
                    conclusion, substitution, premises = item
                    # again, if a single proof was returned, we wrap it in a tuple to make it iterable
                    if isinstance(premises, Proof):
                        premises = (premises,)
                else:
                    raise ValueError("A handler returned tuple must have length 2 or 3")
            elif isinstance(item, LogicObject):
                conclusion = item
                substitution = unifier
                premises = ()
            elif isinstance(item, FormulaSubstitution):
                conclusion = item.formula
                substitution = item.substitution
                premises = ()
            elif isinstance(item, FormulaSubstitutionPremises):
                conclusion = item.formula
                substitution = item.substitution
                premises = (item.premises,) if isinstance(item.premises, Proof) else item.premises
            else:
                raise ValueError(f"A handler cannot return a {type(item)}, read the docs! LogicObjects, "
                                 f"(formula, substitution) pairs, (formula, substitution, Proof/Proofs) triples, "
                                 f"FormulaSubstitution instances or FormulaSubstitutionProofs instances! "
                                 f"What is a {type(item)}????")

            proof = Proof(
                inference_rule=Pondering(listener=self, triggering_formula=formula),
                conclusion=conclusion,
                substitution=substitution,  # TODO remove this, I don't like it anymore
                premises=tuple(itertools.chain((proof,), premises))
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
            if self.pass_substitution_as is None:
                raise ValueError("NOOOOOOOOOO! WHAT HAVE YOU DONE???????")

            args_by_name = {'formula': formula}
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

        if self.pass_substitution_as is not None:
            args_by_name[self.pass_substitution_as] = unifier

        return args_by_name
