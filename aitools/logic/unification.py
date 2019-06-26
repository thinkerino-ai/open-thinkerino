from __future__ import annotations
from copy import copy
from typing import FrozenSet, Dict

from aitools.logic.core import LogicObject, Variable, Expression


class Binding(LogicObject):
    def __init__(self, variables: FrozenSet[Variable], head: LogicObject =None):
        varCount = len(variables)
        if head is None:
            if varCount < 2:
                raise ValueError("If no head is specified there must be at least two variables")
        elif any(v for v in variables if v in head):  # TODO this will be quite slow! how do I solve it?
            raise ValueError("The head of a binding cannot contain its variables")
        if varCount < 1:
            raise ValueError("There must be at least one variable")

        self.head = head
        self.variables = variables

        super().__init__()

    def getBoundObject(self):
        return self.head if self.head is not None else iter(self.variables).__next__()

    @classmethod
    def join(cls, a:Binding, b:Binding, bindingContext=None) -> Binding:
        if a is None or b is None:
            raise ValueError("Bindings cannot be None in a join")

        bindingContext = bindingContext if bindingContext is not None else Substitution()

        aHead = a.head
        bHead = b.head

        if aHead is None and bHead is None:
            newHead = None
        elif aHead is not None and bHead is None:
            newHead = aHead
        elif aHead is None and bHead is not None:
            newHead = bHead
        else:
            unifier = Substitution.unify(a, b, previous=bindingContext)
            if unifier is None:
                raise UnificationError("Unable to unify the heads of the two bindings!")
            else:
                newHead = unifier.applyTo(aHead)

        newVars = frozenset.union(a.variables, b.variables)
        return Binding(newVars, head=newHead)

    def __copy__(self):
        return Binding(copy(self.variables), self.head)

    def __repr__(self):
        return f"Binding({self.variables}, head={self.head})"

    def __str__(self):
        return f"{{{','.join(map(str, self.variables))}}} -> {str(self.head)}"

    def __eq__(self, other):
        return isinstance(other, Binding) and self.head == other.head and self.variables == other.variables

    def __hash__(self):
        return hash((self.head, self.variables))


class Substitution(LogicObject):
    def __init__(self, *bindings:Binding):
        # TODO bindings should be a frozen set
        self._bindings_by_variable : Dict[Variable, Binding] = {}
        for b in bindings:
            self.__declareBinding(b)
        super().__init__()

    def isEmpty(self):
        return len(self._bindings_by_variable) == 0

    def withBindings(self, *bindings):
        res = Substitution()
        res._bindings_by_variable = copy(self._bindings_by_variable)
        for b in bindings:
            res.__declareBinding(b)
        return res

    def __declareBinding(self, binding: Binding) -> None:
        mergedBinding = copy(binding)
        # TODO factory to efficiently build a new substitution with mutable data types
        for v in binding.variables:
            other = self._bindings_by_variable.get(v, None)
            if other is not None:
                mergedBinding = Binding.join(mergedBinding, other, self)

        for v in mergedBinding.variables:
            self._bindings_by_variable[v] = mergedBinding

    def applyTo(self, obj: LogicObject):
        if isinstance(obj, Variable):
            binding: Binding = self._bindings_by_variable.get(obj, None)
            if binding is not None:
                if binding.head is not None:
                    return self.applyTo(binding.head)
                else:
                    return binding.variables.__iter__().__next__()
            else:
                return obj
        elif isinstance(obj, Expression):
            return Expression(*map(self.applyTo, obj.children))
        else:
            return obj

    # TODO maybe add __getitem__, __setitem__ and __contains__ (and then use them in the tests)
    def getBoundObjectFor(self, variable):
        if not isinstance(variable, Variable):
            raise TypeError("Only variables can be bound to an expression")
        return self._bindings_by_variable[variable].getBoundObject()

    @classmethod
    def unify(cls, a, b, *, previous=None):
        subst = previous if previous is not None else Substitution()

        a = subst.applyTo(a)
        b = subst.applyTo(b)

        if a == b:
            return subst
        elif isinstance(a, Variable) and isinstance(b, Variable):
            return subst.withBindings(Binding(frozenset([a, b])))
        elif isinstance(a, Variable) and a not in b:
            return subst.withBindings(Binding(frozenset([a]), head=b))
        elif isinstance(b, Variable) and b not in a:
            return subst.withBindings(Binding(frozenset([b]), head=a))
        elif isinstance(a, Expression) and isinstance(b, Expression) and len(a.children) == len(b.children):
            childUnifier = None
            for aChild, bChild in zip(a.children, b.children):
                childUnifier = Substitution.unify(aChild, bChild, previous=subst)
                if childUnifier is None:
                    return None
                else:
                    subst = childUnifier
            return childUnifier
        else:
            return None

    def __copy__(self):
        res = Substitution()
        res._bindings_by_variable = copy(self._bindings_by_variable)
        return res

    def __repr__(self):
        return f"Substitution({self._bindings_by_variable})"

    def __str__(self):
        return f"[{', '.join(map(str, set(self._bindings_by_variable.values())))}]"

    def __eq__(self, other):
        return all(self.getBoundObjectFor(v)==other.getBoundObjectFor(v) for v in self._bindings_by_variable)

    def __hash__(self):
        return hash(self._bindings_by_variable)


class UnificationError(ValueError):
    """An error that occurs as a consequence of non-unifiable expressions.
    This error does not mean that unification failed, which is an acceptable outcome.
    Rather, it means that unification failed within an operation that requires it to succeed."""
    pass