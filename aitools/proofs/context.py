import threading
from functools import wraps
from inspect import isgeneratorfunction

from aitools.logic import Expression
from aitools.logic.utils import ConstantSource, VariableSource
from aitools.proofs.proof import ProofSet


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


context = Context()
context.kb = None


def prove(formula: Expression, truth: bool = True) -> ProofSet:
    return context.kb.prove(formula, truth)


def contextual(attribute_name, value):
    """Makes a function "contextual".
    The specified context attribute is backed up and replaced with the new value before entering the function,
    and restored after it returns or yields."""
    def decorator(func):
        is_generator = isgeneratorfunction(func)
        @wraps(func)
        def _wrapper(*args, **kwargs):
            nonlocal is_generator
            previous = getattr(context, attribute_name)
            setattr(context, attribute_name, value)

            res = func(*args, **kwargs)

            if is_generator:
                for r in res:
                    setattr(context, attribute_name, previous)
                    yield r
                    previous = getattr(context, attribute_name)
                    setattr(context, attribute_name, value)

            else:
                setattr(context, attribute_name, previous)
                return res

        return _wrapper

    return decorator