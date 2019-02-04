from __future__ import annotations
from copy import copy
from typing import FrozenSet, Dict

def __fail(exception):
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

class Variable(LogicObject):

    def __str__(self):
        return "?v{}".format(self.id)


class Expression(LogicObject):
    def __init__(self, *children:LogicObject):
        if len(children) == 0:
            raise ValueError("There must be at least one child for an expression")
        self.children = [c if isinstance(c, LogicObject) else __fail(ValueError(f"{c} is not a logic object, wrap it if you want to put it in an expression")) for c in children]

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


class Binding(LogicObject):
    def __init__(self, variables: FrozenSet[Variable], head:LogicObject=None):
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
        return f"{self.variables} -> {self.head}"

    def __eq__(self, other):
        return isinstance(other, Binding) and self.head == other.head and self.variables == other.variables

    def __hash__(self):
        return hash((self.head, self.variables))


class Substitution(LogicObject):
    def __init__(self, *bindings:Binding):
        # TODO bindings should be a frozen set
        self.bindings : Dict[Variable, Binding] = {}
        for b in bindings:
            self.__declareBinding(b)
        super().__init__()

    def isEmpty(self):
        return len(self.bindings) == 0

    def withBindings(self, *bindings):
        res = Substitution()
        res.bindings = copy(self.bindings)
        for b in bindings:
            res.__declareBinding(b)
        return res

    def __declareBinding(self, binding: Binding) -> None:
        mergedBinding = copy(binding)
        # TODO factory to efficiently build a new substitution with mutable data types
        for v in binding.variables:
            other = self.bindings.get(v, None)
            if other is not None:
                mergedBinding = Binding.join(mergedBinding, other, self)

        for v in mergedBinding.variables:
            self.bindings[v] = mergedBinding

    def applyTo(self, obj: LogicObject):
        if isinstance(obj, Variable):
            binding: Binding = self.bindings.get(obj, None)
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
        return self.bindings[variable].getBoundObject()

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
        res.bindings = copy(self.bindings)
        return res

    def __repr__(self):
        return f"Substitution({self.bindings})"

    def __str__(self):
        return f"[{map(str,self.bindings)}]"

    def __eq__(self, other):
        return isinstance(other, Substitution) and self.bindings == other.bindings

    def __hash__(self):
        return hash(self.bindings)


class UnificationError(ValueError):
    """An error that occurs as a consequence of non-unifiable expressions.
    This error does not mean that unification failed, which is an acceptable outcome.
    Rather, it means that unification failed within an operation that requires it to succeed."""
    pass
