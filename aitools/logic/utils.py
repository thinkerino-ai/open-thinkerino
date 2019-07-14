from collections.abc import Sequence
from typing import Any

from aitools.logic.unification import Binding, Substitution
from aitools.logic import Variable, Expression, LogicWrapper, LogicObject


def logicObjects(count: int, *, clazz=LogicObject):
    return (clazz() for _ in range(count))


def variables(count: int):
    return (Variable() for _ in range(count))

def wrap(obj: Any):
    if isinstance(obj, LogicObject):
        return obj
    else:
        return LogicWrapper(obj)

class ExpressionMaker:
    @staticmethod
    def makeExpression(obj) -> LogicObject:
        if isinstance(obj, LogicObject):
            return obj
        else:
            # supports only sequences
            if isinstance(obj, Sequence) and not isinstance(obj, str):
                return Expression(*map(ExpressionMaker.makeExpression, obj))
            else:
                return LogicWrapper(obj)

    def __rrshift__(self, other):
        return self.makeExpression(other)


expr: ExpressionMaker = ExpressionMaker()


def binding(head, variables) -> Binding:
    return Binding(frozenset(variables), head=head)


def subst(*bindings) -> Substitution:
    return Substitution(*map(lambda b: binding(b[0], b[1]), bindings))


class VariableSource:
    def __init__(self, **initial_vars: Variable):
        self.__vars = initial_vars

    def __getattr__(self, item):
        if item not in self.__vars:
            self.__vars[item] = val = Variable()
        else:
            val = self.__vars[item]

        return val


variable_source = VariableSource()