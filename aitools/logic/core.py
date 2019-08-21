from __future__ import annotations


def fail(exception):
    raise exception


class LogicObject:
    """An object with a unique ID"""
    _lastID = 0

    def __init__(self):
        self.id = LogicObject._lastID
        LogicObject._lastID = LogicObject._lastID + 1
        super().__init__()

    def __repr__(self):
        return "{}({})".format(type(self).__name__, self.id)

    def __str__(self):
        return "o{}".format(self.id)

    def __contains__(self, obj):
        return False

    def __eq__(self, other):
        return isinstance(other, LogicObject) and other.id == self.id

    def __hash__(self):
        return hash(self.id)

    def __call__(self, *other_children):
        return Expression(self, *other_children)


class LogicWrapper(LogicObject):
    """Wraps an object in a LogicObject"""

    def __init__(self, value):
        self.value = value
        super().__init__()

    def __repr__(self):
        return "LogicWrapper({}, {})".format(self.id, repr(self.value))

    def __str__(self):
        return "{}:{}".format(super().__str__(), str(self.value))

    def __eq__(self, other):
        return (other.id == self.id or
                isinstance(other, LogicWrapper) and other.value == self.value or
                not isinstance(other, LogicObject) and self.value == other)

    def __hash__(self):
        return hash(self.value)

    def __mod__(self, other):
        if isinstance(other, LogicObject):
            return self.value % other.value
        else:
            return self.value % other

    # TODO all other magic methods!

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
