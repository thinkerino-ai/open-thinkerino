from collections.abc import Sequence
from typing import Any

from aitools.logic.unification import Binding, Substitution
from aitools.logic import Variable, Expression, LogicWrapper, LogicObject


def logic_objects(count: int, *, clazz=LogicObject):
    return (clazz() for _ in range(count))


def variables(count: int):
    return (Variable() for _ in range(count))


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

    def __getattr__(self, item):
        if item not in self.__vars:
            self.__vars[item] = val = Variable()
        else:
            val = self.__vars[item]

        return val


class LogicObjectSource:
    def __init__(self, **initial_objects: LogicObject):
        self.__objects = {**initial_objects}

    def __getattr__(self, item):
        if item not in self.__objects:
            self.__objects[item] = val = LogicObject()
        else:
            val = self.__vars[item]

        return val


variable_source = VariableSource()

logic_object_source = LogicObjectSource()