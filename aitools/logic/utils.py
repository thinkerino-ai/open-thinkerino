from . import LogicObject, LogicWrapper, Expression, Variable, Binding, Substitution


def logicObjects(count: int):
    return (LogicObject() for _ in range(count))


def variables(count: int):
    return (Variable() for _ in range(count))


class ExpressionMaker:
    @staticmethod
    def makeExpression(obj) -> LogicObject:
        if isinstance(obj, LogicObject):
            return obj
        else:
            try:
                return Expression(*map(ExpressionMaker.makeExpression, obj))
            except ValueError:
                return LogicWrapper(obj)

    def __rrshift__(self, other):
        return self.makeExpression(other)


expr: ExpressionMaker = ExpressionMaker()


def binding(head, variables) -> Binding:
    return Binding(frozenset(variables), head=head)


def subst(*bindings) -> Substitution:
    return Substitution(*map(lambda b: binding(b[0], b[1]), bindings))
