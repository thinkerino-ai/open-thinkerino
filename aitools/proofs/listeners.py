from __future__ import annotations
from typing import Union, Iterable

from aitools.logic import Expression, Substitution, Variable

class Listener():
    def __init__(self, wrapped_function, *listened_formulas):
        self.wrapped_function = wrapped_function
        self.listened_formulas = listened_formulas
        self.func_arg_names = wrapped_function.__code__.co_varnames[:wrapped_function.__code__.co_argcount]

    def extract_and_call(self, formula):
        if len(self.listened_formulas) == 1:
            return self.arg_extractor_simple(formula)
        else:
            raise NotImplementedError("Not yet implemented soriii")

    def arg_extractor_simple(self, formula: Expression) -> Union[Expression, Iterable[Expression],
                                                                 Listener, Iterable[Listener]]:
        subst = Substitution.unify(formula, self.listened_formulas[0])
        if subst is None:
            return None
        bindings_by_variable_name = {}

        # TODO switch to some public API to get the bindings
        for var in subst._bindings_by_variable:
            bound_object = subst.get_bound_object_for(var)

            # variables do not count as bound object (use a LogicWrapper if you need that)
            if bound_object and not isinstance(bound_object, Variable):
                bindings_by_variable_name[var.name] = bound_object

        prepared_args = {}

        for arg in self.func_arg_names:
            if arg in bindings_by_variable_name:
                prepared_args[arg] = bindings_by_variable_name[arg]

        return self.wrapped_function(**prepared_args)


class _MultiListenerWrapper:
    def __init__(self, wrapped_function, *listeners):
        self.wrapped_function = wrapped_function
        self.listeners = listeners

    def __call__(self, *args, **kwargs):
        return self.wrapped_function(*args, *kwargs)


def listener(*listened_formulas: Expression):
    def decorator(func_or_listeners):
        if isinstance(func_or_listeners, _MultiListenerWrapper):
            return _MultiListenerWrapper(
                func_or_listeners,
                Listener(func_or_listeners.wrapped_function, *listened_formulas),
                *func_or_listeners.listeners)
        else:
            return _MultiListenerWrapper(func_or_listeners, Listener(func_or_listeners, *listened_formulas))

    return decorator
