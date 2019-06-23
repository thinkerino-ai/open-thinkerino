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
        return other.id == self.id

    def __hash__(self):
        return hash(self.id)


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
        return other.id == self.id or isinstance(other, LogicWrapper) and other.value == self.value

    def __hash__(self):
        return hash(self.value)