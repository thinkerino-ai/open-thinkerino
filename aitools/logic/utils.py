from collections.abc import Sequence
from typing import Any, Iterable, Union, Dict

from aitools.logic.unification import Binding, Substitution
from aitools.logic import Variable, Constant, Expression, LogicWrapper, LogicObject


def constants(count_or_names: Union[int, str, Iterable[str]], *, clazz=Constant):
    if isinstance(count_or_names, int):
        return (clazz() for _ in range(count_or_names))
    elif isinstance(count_or_names, str):
        return (clazz(name=name.strip()) for name in count_or_names.split(','))
    else:
        return (clazz(name=name) for name in count_or_names)


def variables(count_or_names: Union[int, str, Iterable[str]]):
    if isinstance(count_or_names, int):
        return (Variable() for _ in range(count_or_names))
    elif isinstance(count_or_names, str):
        return (Variable(name=name.strip()) for name in count_or_names.split(','))
    else:
        return (Variable(name=name) for name in count_or_names)


def wrap(obj: Any):
    if isinstance(obj, LogicObject):
        return obj
    else:
        return LogicWrapper(obj)


def expr(*args) -> LogicObject:
    if len(args) == 0:
        raise ValueError("At least one element!")
    elif len(args) == 1:
        obj = args[0]
    else:
        obj = args

    if isinstance(obj, LogicObject):
        return obj
    else:
        # supports only sequences
        if isinstance(obj, Sequence) and not isinstance(obj, str):
            return Expression(*map(expr, obj))
        else:
            return LogicWrapper(obj)




def binding(head, vars) -> Binding:
    return Binding(frozenset(vars), head=head)


def subst(*bindings) -> Substitution:
    return Substitution(*map(lambda b: binding(b[0], b[1]), bindings))


class VariableSource:
    def __init__(self, **initial_vars: Variable):
        self.__vars = {**initial_vars}

    def __getitem__(self, item) -> Variable:
        if item not in self.__vars:
            self.__vars[item] = val = Variable(name=item)
        else:
            val = self.__vars[item]

        return val

    def __getattr__(self, item) -> Variable:
        return self[item]


class ConstantSource:
    def __init__(self, **initial_constants: Constant):
        self.__constants = {**initial_constants}

    def __getattr__(self, item):
        if item not in self.__constants:
            self.__constants[item] = val = Constant(name=item)
        else:
            val = self.__constants[item]

        return val


def normalize_variables(expression: LogicObject, *, variable_source: VariableSource = None,
                        variable_mapping=None) -> Expression:
    variable_mapping = variable_mapping if variable_mapping is not None else {}
    """Normalizes an expression by either using completely new variables or a standard set"""
    def _inner(obj, mapping):
        if isinstance(obj, Variable):
            result = mapping.get(obj, Variable(name=obj.name) if variable_source is None else variable_source[str(len(mapping))])
            mapping[obj] = result
        elif isinstance(obj, Expression):
            result = Expression(*(_inner(c, mapping) for c in obj.children))
        else:
            result = obj
        return result

    return _inner(expression, variable_mapping)