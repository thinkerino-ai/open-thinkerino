from __future__ import annotations
from typing import Union, Iterable, Optional

from aitools.logic import Expression, Substitution, Variable


class Listener:
    def __init__(self, wrapped_function, listened_formulas, previous_substitution: Substitution = None, priority=0,
                 **_kwargs):
        self.wrapped_function = wrapped_function
        self.listened_formulas = listened_formulas
        self.func_arg_names = wrapped_function.__code__.co_varnames[:wrapped_function.__code__.co_argcount]
        self.previous_substitution = previous_substitution
        self.priority = priority

    def extract_and_call(self, formula):
        if len(self.listened_formulas) == 1:
            return self.arg_extractor_simple(formula)
        else:
            return self.arg_extractor_complex(formula)

    def arg_extractor_simple(self, formula: Expression) -> Optional[Union[Expression, Iterable[Expression],
                                                                 Listener, Iterable[Listener]]]:
        listened_formula = self.listened_formulas[0]
        subst = Substitution.unify(formula, listened_formula, previous=self.previous_substitution)
        if subst is None:
            return None
        prepared_args = self._prepare_arguments(subst)

        return self.wrapped_function(**prepared_args)

    def arg_extractor_complex(self, formula):
        cumulative_substitution = self.previous_substitution
        remaining_formulas = []
        for listened_formula in self.listened_formulas:
            subst = Substitution.unify(formula, listened_formula, previous=cumulative_substitution)
            # if the formula is a match, we extend the substitution, otherwise we leave the formula for the future
            if subst is not None:
                cumulative_substitution = subst
            else:
                remaining_formulas.append(listened_formula)

        if cumulative_substitution is None:
            return None

        if len(remaining_formulas) == 0:
            prepared_args = self._prepare_arguments(cumulative_substitution)
            return self.wrapped_function(**prepared_args)
        else:
            return Listener(self.wrapped_function, remaining_formulas, previous_substitution=cumulative_substitution)

    def _prepare_arguments(self, subst):
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
        return prepared_args


class _MultiListenerWrapper:
    def __init__(self, wrapped_function, *listeners):
        self.wrapped_function = wrapped_function
        self.listeners = listeners

    def __call__(self, *args, **kwargs):
        return self.wrapped_function(*args, *kwargs)


def listener(*listened_formulas: Expression, priority=0):
    def decorator(func_or_listeners):
        if isinstance(func_or_listeners, _MultiListenerWrapper):
            return _MultiListenerWrapper(
                func_or_listeners,
                Listener(func_or_listeners.wrapped_function, listened_formulas, priority=priority),
                *func_or_listeners.listeners)
        else:
            return _MultiListenerWrapper(func_or_listeners,
                                         Listener(func_or_listeners, listened_formulas, priority=priority))

    return decorator
