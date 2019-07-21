"""Some basic symbols"""

# Logic Operators
from aitools.logic import LogicObject, Expression
from aitools.logic.utils import logic_objects


class LogicInfix(LogicObject):
    def __init__(self, function=None):
        super().__init__()
        self.function = function or self.__call__

    """Heavily inspired by (aka copy-pasted from) Infix at https://github.com/ActiveState/code"""
    def __ror__(self, other):
        return LogicInfix(lambda x, self=self, other=other: self.function(other, x))

    def __or__(self, other):
        return self.function(other)

    def __rlshift__(self, other):
        return LogicInfix(lambda x, self=self, other=other: self.function(other, x))

    def __rshift__(self, other):
        return self.function(other)



And, Or, Implies, CoImplies = logic_objects(4, clazz=LogicInfix)
Not, = logic_objects(1, clazz=LogicObject)
