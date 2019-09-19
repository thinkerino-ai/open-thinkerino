from collections.abc import Sequence
from typing import Any, Iterable, Union, Dict

from aitools.logic.unification import Binding, Substitution
from aitools.logic import Variable, Constant, Expression, LogicWrapper, LogicObject


def renew_variables(expression: Expression) -> Expression:
    def _inner(obj, mapping):
        if isinstance(obj, Variable):
            result = mapping.get(obj, Variable())
            mapping[obj] = result
        elif isinstance(obj, Expression):
            result = Expression(*(_inner(c, mapping) for c in obj.children))
        else:
            result = obj
        return result

    return _inner(expression, {})


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

    def __getattr__(self, item) -> Variable:
        if item not in self.__vars:
            self.__vars[item] = val = Variable(name=item)
        else:
            val = self.__vars[item]

        return val


class ConstantSource:
    def __init__(self, **initial_constants: Constant):
        self.__constants = {**initial_constants}

    def __getattr__(self, item):
        if item not in self.__constants:
            self.__constants[item] = val = Constant()
        else:
            val = self.__constants[item]

        return val
