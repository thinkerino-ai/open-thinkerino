from enum import Enum, auto
from typing import Callable, Optional, List, Dict, Any

from aitools.logic import LogicObject, Substitution, Variable, LogicWrapper
from aitools.logic.utils import map_variables_by_name, VariableSource, normalize_variables


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


# TODO make this generic in the handler return type
class Component:
    def __init__(self, *,
                 listened_formula: LogicObject, handler: Callable,
                 argument_mode: HandlerArgumentMode, pass_substitution_as=...,
                 pure: bool, safety: HandlerSafety):

        self._normalization_variable_source = VariableSource()

        self.handler = handler
        listened_formula, _ = normalize_variables(listened_formula)
        self.listened_formula = listened_formula
        self.argument_mode = argument_mode
        self.pure = pure
        self.safety = safety

        self._func_arg_names = handler.__code__.co_varnames[:handler.__code__.co_argcount]

        pass_substitution_as = self.__validate_pass_substitution_as(pass_substitution_as)

        self.pass_substitution_as: Optional[str] = pass_substitution_as

        self.variables_by_name = (
            None if self.argument_mode == HandlerArgumentMode.RAW
            else map_variables_by_name(listened_formula)
        )

        self.__validate_handler_arguments(pass_substitution_as)

    def __validate_pass_substitution_as(self, pass_substitution_as):
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
        return pass_substitution_as

    def __validate_handler_arguments(self, pass_substitution_as):
        if self.handler.__code__.co_posonlyargcount > 0:
            # TODO allow also kw-only args
            raise ValueError("Handlers cannot have positional-only arguments")

        if self.argument_mode == HandlerArgumentMode.RAW:
            if self._func_arg_names != ('formula', self.pass_substitution_as):
                raise ValueError(f"The handler has the wrong argument names {self._func_arg_names}! "
                                 f"{HandlerArgumentMode.RAW} requires the handler to take two arguments: "
                                 f"'formula' and '{pass_substitution_as}' (from the 'pass_substitution_as' arg)")
        else:
            unlistened_arg_names = list(
                arg_name
                for arg_name in self._func_arg_names
                if arg_name not in self.variables_by_name and arg_name != self.pass_substitution_as
            )
            if any(unlistened_arg_names):
                raise ValueError(f"The handler has the wrong argument names {self._func_arg_names}! "
                                 f"Handler arguments {unlistened_arg_names} "
                                 f"are not present in formula {self.listened_formula}")

    def _map_substitution_to_function_args(self, substitution: Substitution, func_arg_names: List[str],
                                           normalization_mapping: Dict[Variable, Variable]) -> Dict[str, Any] :
        prepared_args = {}
        for arg in func_arg_names:
            if arg in self.variables_by_name:
                mapped_variable = normalization_mapping.get(self.variables_by_name[arg], None)
                if mapped_variable is None:
                    raise ValueError("What is happening here?")
                prepared_args[arg] = substitution.get_bound_object_for(mapped_variable)
        return prepared_args

    def _extract_args_by_name(self, formula: LogicObject, unifier: Substitution,
                              normalization_mapping: Dict[Variable, Variable]) -> Dict[str, Any]:
        if self.argument_mode == HandlerArgumentMode.RAW:
            if self.pass_substitution_as is None:
                raise ValueError("NOOOOOOOOOO! WHAT HAVE YOU DONE???????")

            args_by_name = {'formula': formula}
        else:
            args_by_name = self._map_substitution_to_function_args(substitution=unifier,
                                                                   func_arg_names=self._func_arg_names,
                                                                   normalization_mapping=normalization_mapping)

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

    def __str__(self):
        return f"{self.__class__.__name__}({self.handler.__module__}.{self.handler.__name__})"