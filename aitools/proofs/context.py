import threading

from aitools.logic.utils import LogicObjectSource, VariableSource


def make_property(attr_name):
    def _make_getter(attr):
        def getter(self):
            return getattr(self._local, attr)
        return getter

    def _make_setter(attr):
        def setter(self, value):
            setattr(self._local, attr, value)

        return setter

    return property(_make_getter(attr_name), _make_setter(attr_name))


class Context():
    def __init__(self):
        self._local = threading.local()

    kb = make_property('kb')
    predicate_source = make_property('predicate_source')
    variable_source = make_property('variable_source')


context = Context()
context.predicate_source = LogicObjectSource()
context.variable_source = VariableSource()
