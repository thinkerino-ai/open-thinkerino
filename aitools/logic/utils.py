import itertools
from collections.abc import Sequence
from typing import Any, Iterable, Union, Dict, Set, Tuple

from aitools.logic.language import Language
from aitools.logic.unification import Binding, Substitution
from aitools.logic.core import Variable, Constant, Expression, LogicObject, LogicWrapper


def constants(count_or_names: Union[int, str, Iterable[str]], *, language: Language, clazz=Constant):
    if isinstance(count_or_names, int):
        return (clazz(language=language) for _ in range(count_or_names))
    elif isinstance(count_or_names, str):
        return (clazz(name=name.strip(), language=language) for name in count_or_names.split(','))
    else:
        return (clazz(name=name, language=language) for name in count_or_names)


def variables(count_or_names: Union[int, str, Iterable[str]], *, language: Language):
    if isinstance(count_or_names, int):
        return (Variable(language=language) for _ in range(count_or_names))
    elif isinstance(count_or_names, str):
        return (Variable(name=name.strip(), language=language) for name in count_or_names.split(','))
    else:
        return (Variable(name=name, language=language) for name in count_or_names)


def wrap(obj: Any):
    if isinstance(obj, LogicObject):
        return obj
    else:
        return LogicWrapper(obj)


def expr(*args) -> Expression:
    if len(args) == 0:
        raise ValueError("At least one element!")

    return Expression(
        *map(
            lambda el: expr(*el) if isinstance(el, Sequence) and not isinstance(el, str) else wrap(el),
            args
        )
    )


def binding(head, vars) -> Binding:
    return Binding(frozenset(vars), head=head)


def subst(*bindings) -> Substitution:
    return Substitution(*map(lambda b: binding(b[0], b[1]), bindings))


class VariableSource:
    def __init__(self, *, language: Language):
        self.language = language
        self.__vars = {}

    def __getitem__(self, item) -> Variable:
        if item not in self.__vars:
            self.__vars[item] = val = Variable(name=item, language=self.language)
        else:
            val = self.__vars[item]

        return val

    def __getattr__(self, item) -> Variable:
        return self[item]


class ConstantSource:
    def __init__(self, *, language: Language):
        self.language = language
        self.__constants = {}

    def __getattr__(self, item):
        if item not in self.__constants:
            self.__constants[item] = val = Constant(name=item, language=self.language)
        else:
            val = self.__constants[item]

        return val


def normalize_variables(expression: LogicObject, *, variable_source: VariableSource = None,
                        variable_mapping=None, language: Language = None) -> Tuple[Expression, Dict[Variable, Variable]]:
    """Normalizes an expression by either using completely new variables or a standard set"""
    if (variable_source is None) == (language is None):
        raise ValueError("Either pass a variable source or a language!")

    variable_mapping = variable_mapping if variable_mapping is not None else {}
    def _inner(obj, mapping):
        if isinstance(obj, Variable):
            result = mapping.get(obj, Variable(name=obj.name, language=language) if variable_source is None else variable_source[str(len(mapping))])
            mapping[obj] = result
        elif isinstance(obj, Expression):
            result = Expression(*(_inner(c, mapping) for c in obj.children))
        else:
            result = obj
        return result

    return _inner(expression, variable_mapping), variable_mapping


def all_variables_in(obj: LogicObject) -> Iterable[Variable]:
    if isinstance(obj, Variable):
        yield obj
    elif isinstance(obj, Expression):
        yield from itertools.chain.from_iterable(all_variables_in(c) for c in obj.children)


def all_unique_variables_in(obj: LogicObject) -> Set[Variable]:
    return set(all_variables_in(obj))


def map_variables_by_name(obj: LogicObject) -> Dict[str, Variable]:
    result = {}

    for v in all_variables_in(obj):
        if v.name is not None:
            already_present = result.get(v.name)
            if already_present is None:
                result[v.name] = v
            else:
                if v == already_present:
                    continue
                else:
                    raise ValueError(f"Found two homonymous variables with name {v.name} in {obj}")

    return result
