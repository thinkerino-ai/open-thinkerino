from __future__ import annotations

import abc
import dataclasses
import typing
import uuid

from aitools.logic.language import Language


def fail(exception):
    raise exception


class LogicObject(abc.ABC):
    pass


@dataclasses.dataclass(frozen=True)
class Identifier:
    language: Language
    sequential_id: int


class Symbol(LogicObject, abc.ABC):

    def __init__(self, *, name: typing.Optional[str] = None, language: Language):
        if name is not None and not (isinstance(name, str) and name):
            raise ValueError("Symbol name must be a non-empty string!")

        self.id: Identifier = Identifier(language=language, sequential_id=language.get_next())
        self.name = name

    def __call__(self, *other_children) -> Expression:
        return Expression(self, *other_children)

    def __eq__(self, other):
        if not isinstance(other, Symbol):
            return NotImplemented
        return other.id == self.id

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        fake_lang = Language(_language_id=self.id.language._id, _next_id=None)
        fake_identifier = Identifier(language=fake_lang, sequential_id=self.id.sequential_id)
        return f"{self.__class__.__name__}(name={repr(self.name)}, id={repr(fake_identifier)})"


class Constant(Symbol):
    def __str__(self):
        if self.name is not None:
            return "{}{}".format(self.name, self.id.sequential_id)
        else:
            return "o{}".format(self.id.sequential_id)


class Variable(Symbol):
    def __str__(self):
        if self.name is not None:
            return "?{}{}".format(self.name, self.id.sequential_id)
        else:
            return "?v{}".format(self.id.sequential_id)


class Expression(LogicObject):
    def __init__(self, *children: LogicObject):
        if len(children) == 0:
            raise ValueError("There must be at least one child for an expression")
        self.children = tuple(c if isinstance(c, LogicObject) else fail(ValueError(f"{c} is not a logic object, wrap it if you want to put it in an expression")) for c in children)

        super().__init__()

    def __repr__(self):
        return "Expression({})".format(self.children)

    def __str__(self):
        return "({})".format(", ".join(map(str, self.children)))

    def __contains__(self, obj):
        return any(
            obj == child or (isinstance(child, Expression) and obj in child)
            for child in self.children
        )

    def __eq__(self, other):
        if not isinstance(other, Expression) or len(self.children) != len(other.children):
            return False

        for a, b in zip(self.children, other.children):
            if a != b:
                return False

        return True

    def __hash__(self):
        # TODO store this so that it is calculated only once
        return hash(self.children)

    @property
    def size(self):
        return 1 + sum(c.size if isinstance(c, Expression) else 1
                       for c in self.children)


class LogicWrapper(LogicObject):
    """Wraps an object in a LogicObject"""

    def __init__(self, value):
        if not isinstance(value, typing.Hashable):
            raise ValueError("A wrapped value must be hashable")
        self.value = value
        super().__init__()

    def __repr__(self):
        return "LogicWrapper({})".format(repr(self.value))

    def __str__(self):
        return "{{{}}}".format(str(self.value))

    def __eq__(self, other):
        return (isinstance(other, LogicWrapper) and other.value == self.value or
                not isinstance(other, LogicWrapper) and self.value == other)

    def __hash__(self):
        # TODO something needs to be done if self.value is not hashable!
        return hash(self.value)

    @staticmethod
    def __magic_binary(method, other):
        if isinstance(other, LogicWrapper):
            return LogicWrapper(method(other.value))
        else:
            return LogicWrapper(method(other))

    def __add__(self, other):
        return self.__magic_binary(self.value.__add__, other)

    def __sub__(self, other):
        return self.__magic_binary(self.value.__sub__, other)

    def __mul__(self, other):
        return self.__magic_binary(self.value.__mul__, other)

    def __truediv__(self, other):
        return self.__magic_binary(self.value.__truediv__, other)

    def __floordiv__(self, other):
        return self.__magic_binary(self.value.__floordiv__, other)

    def __mod__(self, other):
        return self.__magic_binary(self.value.__mod__, other)

    def __pow__(self, other):
        return self.__magic_binary(self.value.__pow__, other)

    def __rshift__(self, other):
        return self.__magic_binary(self.value.__rshift__, other)

    def __lshift__(self, other):
        return self.__magic_binary(self.value.__lshift__, other)

    def __and__(self, other):
        return self.__magic_binary(self.value.__and__, other)

    def __or__(self, other):
        return self.__magic_binary(self.value.__or__, other)

    def __xor__(self, other):
        return self.__magic_binary(self.value.__xor__, other)

    def __radd__(self, other):
        return self.__magic_binary(self.value.__radd__, other)

    def __rsub__(self, other):
        return self.__magic_binary(self.value.__rsub__, other)

    def __rmul__(self, other):
        return self.__magic_binary(self.value.__rmul__, other)

    def __rtruediv__(self, other):
        return self.__magic_binary(self.value.__rtruediv__, other)

    def __rfloordiv__(self, other):
        return self.__magic_binary(self.value.__rfloordiv__, other)

    def __rmod__(self, other):
        return self.__magic_binary(self.value.__rmod__, other)

    def __rpow__(self, other):
        return self.__magic_binary(self.value.__rpow__, other)

    def __rrshift__(self, other):
        return self.__magic_binary(self.value.__rrshift__, other)

    def __rlshift__(self, other):
        return self.__magic_binary(self.value.__rlshift__, other)

    def __rand__(self, other):
        return self.__magic_binary(self.value.__rand__, other)

    def __ror__(self, other):
        return self.__magic_binary(self.value.__ror__, other)

    def __rxor__(self, other):
        return self.__magic_binary(self.value.__rxor__, other)

    def __lt__(self, other):
        return self.__magic_binary(self.value.__lt__, other)

    def __gt__(self, other):
        return self.__magic_binary(self.value.__gt__, other)

    def __le__(self, other):
        return self.__magic_binary(self.value.__le__, other)

    def __ge__(self, other):
        return self.__magic_binary(self.value.__ge__, other)

    def __neg__(self):
        return self.value.__neg__()

    def __pos__(self, other):
        return self.value.__pos__()

    def __invert__(self, other):
        return self.value.__invert__()

