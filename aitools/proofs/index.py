from __future__ import annotations

from aitools.logic import Expression, LogicObject, Variable
from aitools.utils.abstruse_index import WILDCARD


# TODO: typing
# TODO: make this lazy so that it is calculated when it is traversed (otherwise searching for very deep formulas in the
#  AbstruseIndex could be inefficient)
def make_key(formula: LogicObject):
    res = []

    def inner(formula, level):
        if len(res) == level:
            res.append([])

        if isinstance(formula, Expression):
            res[level].append(len(formula.children))
            for child in formula.children:
                inner(child, level + 1)
        elif isinstance(formula, Variable):
            res[level].append(WILDCARD)
        else:
            res[level].append(formula)

    inner(formula, 0)
    return res
