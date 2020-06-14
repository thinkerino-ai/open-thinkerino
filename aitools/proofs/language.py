"""Some basic symbols"""

# Logic Operators
import uuid

from aitools.logic.core import LogicObject, LogicWrapper, Constant
from aitools.logic.language import Language
from aitools.logic.utils import constants

# TODO decide what the best approach for this would be, until then, 42 is the answer
language = Language(_language_id=uuid.UUID(int=42), _next_id=0)


class MagicPredicate(Constant):
    def __call__(self, *other_children):
        return super().__call__(*(c if isinstance(c, LogicObject) else LogicWrapper(c) for c in other_children))


class LogicOperator(Constant):
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


class LogicInfix(LogicOperator):
    def __init__(self, function=None, **kwargs):
        super().__init__(**kwargs)
        self.function = function or self.__call__

    """Heavily inspired by (aka copy-pasted from) Infix at https://github.com/ActiveState/code"""
    def __ror__(self, other):
        return LogicInfix(lambda x, self=self, other=other: self.function(other, x))

    def __or__(self, other):
        return self.function(other)

    def __rlshift__(self, other):
        return LogicInfix(lambda x, self=self, other=other: self.function(other, x), language=language)

    def __rshift__(self, other):
        return self.function(other)


And, Or, Implies, CoImplies = constants('And, Or, Implies, CoImplies', clazz=LogicInfix, language=language)
# TODO magic operator ~formula to produce the same as Not(Formula)
Not = LogicOperator(name='Not', language=language)
