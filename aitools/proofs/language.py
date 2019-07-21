"""Some basic symbols"""

# Logic Operators
from aitools.logic import LogicObject, Expression
from aitools.logic.utils import logic_objects


class LogicSymbol(LogicObject):
    def __call__(self, *other_children):
        return Formula(self, *other_children)


And, Or, Implies, CoImplies, Not = logic_objects(5, clazz=LogicSymbol)


class Formula(Expression):

    def __rshift__(self, other):
        if isinstance(other, Expression):
            return Implies(self, other)
