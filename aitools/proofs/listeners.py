from functools import wraps

from aitools.logic import Expression, Substitution, Variable


class Listener:
    def __init__(self, *listened_formulas: Expression):
        if len(listened_formulas) < 1:
            raise ValueError("Listeners require at least one formula")
        self.listened_formulas = tuple(listened_formulas)

    def __call__(self, func):
        if isinstance(func, Listener):
            raise NotImplementedError("Not yet implemented, soriii :P")

        # TODO should we also allow kwargs?
        func_arg_names = func.__code__.co_varnames[:func.__code__.co_argcount]

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        def arg_extractor_simple(formula):
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

            for arg in func_arg_names:
                if arg in bindings_by_variable_name:
                    prepared_args[arg] = bindings_by_variable_name[arg]

            return wrapper(**prepared_args)

        def arg_extractor_complex(formula):
            # TODO implement! it should return a new listener
            raise NotImplementedError("Not implemented yet, soriii :P")

        if len(self.listened_formulas) == 1:
            wrapper._arg_extractor = arg_extractor_simple
        else:
            wrapper._arg_extractor = arg_extractor_complex

        return wrapper

# just an alias
listener = Listener
