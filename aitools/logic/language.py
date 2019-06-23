from __future__ import annotations

from aitools.logic.core import fail, LogicObject


class Variable(LogicObject):

    def __str__(self):
        return "?v{}".format(self.id)


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
        return any(obj == child or obj in child for child in self.children)

    def __eq__(self, other):
        if not isinstance(other, Expression) or len(self.children) != len(other.children):
            return False

        for a, b in zip(self.children, other.children):
            if a != b:
                return False

        return True

    def __hash__(self):
        return hash(self.children)


