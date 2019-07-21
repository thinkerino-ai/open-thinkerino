from __future__ import annotations
from copy import copy
from typing import FrozenSet, Dict

from aitools.logic.core import LogicObject, Variable, Expression


class Binding(LogicObject):
    def __init__(self, variables: FrozenSet[Variable], head: LogicObject = None):
        var_count = len(variables)
        if head is None:
            if var_count < 2:
                raise ValueError("If no head is specified there must be at least two variables")
        elif any(v for v in variables if v in head):  # TODO this will be quite slow! how do I solve it?
            raise ValueError("The head of a binding cannot contain its variables")
        if var_count < 1:
            raise ValueError("There must be at least one variable")

        self.head = head
        self.variables = variables

        super().__init__()

    def get_bound_object_for(self):
        return self.head if self.head is not None else iter(self.variables).__next__()

    @classmethod
    def join(cls, a: Binding, b: Binding, binding_context=None) -> Binding:
        if a is None or b is None:
            raise ValueError("Bindings cannot be None in a join")

        binding_context = binding_context if binding_context is not None else Substitution()

        a_head = a.head
        b_head = b.head

        if a_head is None and b_head is None:
            new_head = None
        elif a_head is not None and b_head is None:
            new_head = a_head
        elif a_head is None and b_head is not None:
            new_head = b_head
        else:
            unifier = Substitution.unify(a, b, previous=binding_context)
            if unifier is None:
                raise UnificationError("Unable to unify the heads of the two bindings!")
            else:
                new_head = unifier.apply_to(a_head)

        new_vars = frozenset.union(a.variables, b.variables)
        return Binding(new_vars, head=new_head)

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
    def __init__(self, *bindings: Binding):
        # TODO bindings should be a frozen set
        self._bindings_by_variable: Dict[Variable, Binding] = {}
        for b in bindings:
            self.__declare_binding(b)
        super().__init__()

    def is_empty(self):
        return len(self._bindings_by_variable) == 0

    def with_bindings(self, *bindings):
        res = Substitution()
        res._bindings_by_variable = copy(self._bindings_by_variable)
        for b in bindings:
            res.__declare_binding(b)
        return res

    def __declare_binding(self, binding: Binding) -> None:
        merged_binding = copy(binding)
        # TODO factory to efficiently build a new substitution with mutable data types
        for v in binding.variables:
            other = self._bindings_by_variable.get(v, None)
            if other is not None:
                merged_binding = Binding.join(merged_binding, other, self)

        for v in merged_binding.variables:
            self._bindings_by_variable[v] = merged_binding

    def apply_to(self, obj: LogicObject):
        if isinstance(obj, Variable):
            binding: Binding = self._bindings_by_variable.get(obj, None)
            if binding is not None:
                if binding.head is not None:
                    return self.apply_to(binding.head)
                else:
                    return binding.variables.__iter__().__next__()
            else:
                return obj
        elif isinstance(obj, Expression):
            return Expression(*map(self.apply_to, obj.children))
        else:
            return obj

    # TODO maybe add __getitem__, __setitem__ and __contains__ (and then use them in the tests)
    def get_bound_object_for(self, variable):
        if not isinstance(variable, Variable):
            raise TypeError("Only variables can be bound to an expression")
        return self._bindings_by_variable[variable].get_bound_object_for()

    @classmethod
    def unify(cls, a, b, *, previous=None):
        subst = previous if previous is not None else Substitution()

        a = subst.apply_to(a)
        b = subst.apply_to(b)

        if a == b:
            return subst
        elif isinstance(a, Variable) and isinstance(b, Variable):
            return subst.with_bindings(Binding(frozenset([a, b])))
        elif isinstance(a, Variable) and a not in b:
            return subst.with_bindings(Binding(frozenset([a]), head=b))
        elif isinstance(b, Variable) and b not in a:
            return subst.with_bindings(Binding(frozenset([b]), head=a))
        elif isinstance(a, Expression) and isinstance(b, Expression) and len(a.children) == len(b.children):
            child_unifier = None
            for a_child, b_child in zip(a.children, b.children):
                child_unifier = Substitution.unify(a_child, b_child, previous=subst)
                if child_unifier is None:
                    return None
                else:
                    subst = child_unifier
            return child_unifier
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

    def __eq__(self, other: Substitution):
        return all(self.get_bound_object_for(v) == other.get_bound_object_for(v) for v in self._bindings_by_variable)

    def __hash__(self):
        return hash(self._bindings_by_variable)


class UnificationError(ValueError):
    """An error that occurs as a consequence of non-unifiable expressions.
    This error does not mean that unification failed, which is an acceptable outcome.
    Rather, it means that unification failed within an operation that requires it to succeed."""
    pass
