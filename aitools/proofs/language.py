"""Some basic symbols"""

# Logic Operators
from aitools.logic import LogicObject, LogicWrapper, Constant
from aitools.logic.utils import constants


class MagicPredicate(LogicObject):
    def __call__(self, *other_children):
        return super().__call__(*(c if isinstance(c, LogicObject) else LogicWrapper(c) for c in other_children))


class LogicInfix(Constant):
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

    def __repr__(self):
        if self.name:
            return "{}({})".format(type(self).__name__, self.name)
        else:
            return "{}{}".format(type(self).__name__, self.id)

    def __str__(self):
        if self.name:
            return "{}".format(self.name)
        else:
            return repr(self)


And, Or, Implies, CoImplies = constants(4, clazz=LogicInfix)
# TODO magic operator ~formula to produce the same as Not(Formula)
Not = Constant()
