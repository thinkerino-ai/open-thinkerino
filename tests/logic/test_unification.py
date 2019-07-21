import unittest
from typing import Optional

from aitools.logic import Substitution, Variable
from aitools.logic.core import LogicObject
from aitools.logic.utils import logic_objects, expr, variables, subst, binding, wrap


class TestUnification(unittest.TestCase):

    def assertUnificationResult(self, e1: LogicObject, e2: LogicObject, expected_result: Optional[Substitution], *,
                                previous: Substitution = None):
        result = Substitution.unify(e1, e2, previous=previous)
        if expected_result is not None:
            self.assertIsNotNone(result)
        self.assertEqual(result, expected_result,
                         f"Unification between {e1} and {e2} should give {expected_result}, got {result} instead")

    def testUnificationBetweenLogicObjectsFailure(self):
        a, b = logic_objects(2)

        self.assertUnificationResult(a, b, None)

    def testUnificationBetweenLogicObjectsSuccess(self):
        a, = logic_objects(1)

        expected_result = subst()
        self.assertUnificationResult(a, a, expected_result)

    def testUnificationBetweenExpressionsSuccess(self):
        a, b, c, d = logic_objects(4)
        e1 = (a, (b, c), d) >> expr
        e2 = (a, (b, c), d) >> expr

        expected_result = subst()
        self.assertUnificationResult(e1, e2, expected_result)

    def testUnificationBetweenExpressionsFailure(self):
        a, b, c, d = logic_objects(4)
        e1 = (a, (b, c), d) >> expr
        e2 = (a, (b, c), a) >> expr

        self.assertUnificationResult(e1, e2, None)

    def testUnificationWithVariablesSuccessSimple(self):
        v1, = variables(1)
        a, b, c, d = logic_objects(4)

        expr_d = [d] >> expr
        e1 = (a, (b, c), expr_d) >> expr

        expected_result = subst((e1, [v1]))

        self.assertUnificationResult(v1, e1, expected_result)

    def testUnificationWithVariablesSuccessComplex(self):
        v1, v2 = variables(2)
        a, b, c, d = logic_objects(4)

        expr_d = [d] >> expr
        e1 = (a, (b, c), expr_d) >> expr
        e2 = (a, (v1, c), v2) >> expr

        expected_result = subst((b, [v1]), (expr_d, [v2]))

        self.assertUnificationResult(e1, e2, expected_result)

    def testUnificationWithVariablesFailureConflict(self):
        v1, = variables(1)
        a, b, c, d = logic_objects(4)

        expr_d = [d] >> expr
        e1 = (a, (b, c), expr_d) >> expr
        e3 = (a, (v1, c), v1) >> expr

        self.assertUnificationResult(e1, e3, None)

    def testUnificationWithVariablesSuccessEquality(self):
        v1, v2 = variables(2)
        a, c = logic_objects(2)

        e2 = (a, (v1, c), v2) >> expr
        e3 = (a, (v1, c), v1) >> expr

        expected_result = subst((None, [v1, v2]))

        self.assertUnificationResult(e2, e3, expected_result)

    def testUnificationWithVariablesFailureContained(self):
        v1, v2 = variables(2)
        a, c, d = logic_objects(3)

        expr_d = [d] >> expr
        e2 = (a, (v1, c), v2) >> expr
        e4 = (a, v1, expr_d) >> expr

        self.assertUnificationResult(e2, e4, None)

    def testUnificationWithVariablesSuccessSameExpression(self):
        v1, v2 = variables(2)
        a, b, c, d = logic_objects(4)

        bc_expr1 = (b, c) >> expr
        bc_expr2 = (b, c) >> expr
        e1 = (a, bc_expr1, v1, d) >> expr
        e2 = (a, v2, bc_expr2, d) >> expr

        expected_result = subst((bc_expr1, [v1]), (bc_expr2, [v2]))

        self.assertUnificationResult(e1, e2, expected_result)

    def testUnificationWithPreviousSimpleSucceeding(self):
        x = Variable()
        a, b, c, d = logic_objects(4)

        bc_expr = (b, c) >> expr
        e1 = (a, bc_expr, d) >> expr
        e2 = (a, x, d) >> expr

        previous = subst((bc_expr, [x]))

        self.assertUnificationResult(e1, e2, previous, previous=previous)

    def testUnificationWithPreviousSimpleFailing(self):
        x = Variable()
        a, b, c, d = logic_objects(4)

        bc_expr = (b, c) >> expr
        e1 = (a, bc_expr, d) >> expr
        e2 = (a, x, d) >> expr

        previous = subst((b, [x]))

        self.assertUnificationResult(e1, e2, None, previous=previous)

    def testUnificationWithPreviousSuccessBoundToSameExpression(self):
        x, y, z = variables(3)
        a, d = logic_objects(2)

        e2 = (a, x, z) >> expr
        e3 = (a, y, d) >> expr

        previous = subst((a, [x]), (a, [y]))

        expected_result = previous.with_bindings(binding(d, [z]))

        self.assertUnificationResult(e2, e3, expected_result, previous=previous)

    def testUnificationWithPreviousSuccessBoundToUnifiableExpressions(self):
        x, y, z = variables(3)
        a, b, c, d = logic_objects(4)

        bc_expr = (b, c) >> expr
        bz_expr = (b, z) >> expr
        e2 = (a, x, d) >> expr
        e3 = (a, y, d) >> expr

        previous = subst((bc_expr, [x]), (bz_expr, [y]))

        expected_result = previous.with_bindings(binding(c, [z]))

        self.assertUnificationResult(e2, e3, expected_result, previous=previous)

    def testUnificationWithPreviousFailureBoundToDifferentExpressions(self):
        x, y = variables(2)
        a, b, d = logic_objects(3)

        e2 = (a, x, d) >> expr
        e3 = (a, y, d) >> expr

        previous = subst((a, [x]), (b, [y]))

        self.assertUnificationResult(e2, e3, None, previous=previous)

    def testUnificationWithPrevious(self):
        w, x, y, z = variables(4)
        a, d = logic_objects(2)

        e2 = (a, x, d) >> expr
        e3 = (a, y, d) >> expr

        previous = subst((None, [x, z]), (None, [y, w]))

        expected_result = subst((None, [w, x, y, z]))

        self.assertUnificationResult(e2, e3, expected_result, previous=previous)

    def testUnificationWithRepeatedConstants(self):
        v1 = Variable()

        e1 = (2, v1) >> expr
        e2 = (2, "hi") >> expr

        expected_result = subst((wrap("hi"), [v1]))
        self.assertUnificationResult(e1, e2, expected_result)

    def testUnificationWeirdFailingCase(self):
        v1, v2 = variables(2)
        c, d = logic_objects(2)
        e1 = ("hello", ("yay", c), [d]) >> expr  # alternative syntax: ("hello", (b, c), (d,)) >> expr
        e2 = ("hello", (v1, c), v2) >> expr

        expected_result = subst((wrap("yay"), [v1]), ([d] >> expr, [v2]))

        self.assertUnificationResult(e1, e2, expected_result)
