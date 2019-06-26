import unittest
from typing import Optional

from aitools.logic import Substitution, LogicObject, Variable
from aitools.logic.utils import logicObjects, expr, variables, subst, binding, wrap


class TestUnification(unittest.TestCase):

    def assertUnificationResult(self, e1: LogicObject, e2: LogicObject, expectedResult: Optional[Substitution], *,
                                previous: Substitution = None):
        result = Substitution.unify(e1, e2, previous=previous)
        if expectedResult is not None:
            self.assertIsNotNone(result)
        self.assertEqual(result, expectedResult,
                         f"Unification between {e1} and {e2} should give {expectedResult}, got {result} instead")

    def testUnificationBetweenLogicObjectsFailure(self):
        a, b = logicObjects(2)

        self.assertUnificationResult(a, b, None)

    def testUnificationBetweenLogicObjectsSuccess(self):
        a, = logicObjects(1)

        expectedResult = subst()
        self.assertUnificationResult(a, a, expectedResult)

    def testUnificationBetweenExpressionsSuccess(self):
        a, b, c, d = logicObjects(4)
        e1 = (a, (b, c), d) >> expr
        e2 = (a, (b, c), d) >> expr

        expectedResult = subst()
        self.assertUnificationResult(e1, e2, expectedResult)

    def testUnificationBetweenExpressionsFailure(self):
        a, b, c, d = logicObjects(4)
        e1 = (a, (b, c), d) >> expr
        e2 = (a, (b, c), a) >> expr

        self.assertUnificationResult(e1, e2, None)

    def testUnificationWithVariablesSuccessSimple(self):
        v1, = variables(1)
        a, b, c, d = logicObjects(4)

        expr_d = [d] >> expr
        e1 = (a, (b, c), expr_d) >> expr

        expectedResult = subst((e1, [v1]))

        self.assertUnificationResult(v1, e1, expectedResult)

    def testUnificationWithVariablesSuccessComplex(self):
        v1, v2 = variables(2)
        a, b, c, d = logicObjects(4)

        expr_d = [d] >> expr
        e1 = (a, (b, c), expr_d) >> expr
        e2 = (a, (v1, c), v2) >> expr

        expectedResult = subst((b, [v1]), (expr_d, [v2]))

        self.assertUnificationResult(e1, e2, expectedResult)

    def testUnificationWithVariablesFailureConflict(self):
        v1, = variables(1)
        a, b, c, d = logicObjects(4)

        expr_d = [d] >> expr
        e1 = (a, (b, c), expr_d) >> expr
        e3 = (a, (v1, c), v1) >> expr

        self.assertUnificationResult(e1, e3, None)

    def testUnificationWithVariablesSuccessEquality(self):
        v1, v2 = variables(2)
        a, c = logicObjects(2)

        e2 = (a, (v1, c), v2) >> expr
        e3 = (a, (v1, c), v1) >> expr

        expectedResult = subst((None, [v1, v2]))

        self.assertUnificationResult(e2, e3, expectedResult)

    def testUnificationWithVariablesFailureContained(self):
        v1, v2 = variables(2)
        a, c, d = logicObjects(3)

        expr_d = [d] >> expr
        e2 = (a, (v1, c), v2) >> expr
        e4 = (a, v1, expr_d) >> expr

        self.assertUnificationResult(e2, e4, None)

    def testUnificationWithVariablesSuccessSameExpression(self):
        v1, v2 = variables(2)
        a, b, c, d = logicObjects(4)

        bcExpr1 = (b, c) >> expr
        bcExpr2 = (b, c) >> expr
        e1 = (a, bcExpr1, v1, d) >> expr
        e2 = (a, v2, bcExpr2, d) >> expr

        expectedResult = subst((bcExpr1, [v1]), (bcExpr2, [v2]))

        self.assertUnificationResult(e1, e2, expectedResult)

    def testUnificationWithPreviousSimpleSucceeding(self):
        x = Variable()
        a, b, c, d = logicObjects(4)

        bcExpr = (b, c) >> expr
        e1 = (a, bcExpr, d) >> expr
        e2 = (a, x, d) >> expr

        previous = subst((bcExpr, [x]))

        self.assertUnificationResult(e1, e2, previous, previous=previous)

    def testUnificationWithPreviousSimpleFailing(self):
        x = Variable()
        a, b, c, d = logicObjects(4)

        bcExpr = (b, c) >> expr
        e1 = (a, bcExpr, d) >> expr
        e2 = (a, x, d) >> expr

        previous = subst((b, [x]))

        self.assertUnificationResult(e1, e2, None, previous=previous)

    def testUnificationWithPreviousSuccessBoundToSameExpression(self):
        x, y, z = variables(3)
        a, d = logicObjects(2)

        e2 = (a, x, z) >> expr
        e3 = (a, y, d) >> expr

        previous = subst((a, [x]), (a, [y]))

        expectedResult = previous.withBindings(binding(d, [z]))

        self.assertUnificationResult(e2, e3, expectedResult, previous=previous)

    def testUnificationWithPreviousSuccessBoundToUnifiableExpressions(self):
        x, y, z = variables(3)
        a, b, c, d = logicObjects(4)

        bcExpr = (b, c) >> expr
        bzExpr = (b, z) >> expr
        e2 = (a, x, d) >> expr
        e3 = (a, y, d) >> expr

        previous = subst((bcExpr, [x]), (bzExpr, [y]))

        expectedResult = previous.withBindings(binding(c, [z]))

        self.assertUnificationResult(e2, e3, expectedResult, previous=previous)

    def testUnificationWithPreviousFailureBoundToDifferentExpressions(self):
        x, y = variables(2)
        a, b, d = logicObjects(3)

        e2 = (a, x, d) >> expr
        e3 = (a, y, d) >> expr

        previous = subst((a, [x]), (b, [y]))

        self.assertUnificationResult(e2, e3, None, previous=previous)

    def testUnificationWithPrevious(self):
        w, x, y, z = variables(4)
        a, d = logicObjects(2)

        e2 = (a, x, d) >> expr
        e3 = (a, y, d) >> expr

        previous = subst((None, [x, z]), (None, [y, w]))

        expectedResult = subst((None, [w, x, y, z]))

        self.assertUnificationResult(e2, e3, expectedResult, previous=previous)

    def testUnificationWithRepeatedConstants(self):
        v1 = Variable()

        e1 = (2, v1) >> expr
        e2 = (2, "hi") >> expr

        expectedResult = subst((wrap("hi"), [v1]))
        self.assertUnificationResult(e1, e2, expectedResult)

    def testUnificationWeirdFailingCase(self):
        v1, v2 = variables(2)
        c, d = logicObjects(2)
        e1 = ("hello", ("yay", c), [d]) >> expr # alternative syntax: ("hello", (b, c), (d,)) >> expr
        e2 = ("hello", (v1, c), v2) >> expr
 
        expectedResult = subst((wrap("yay"), [v1]), ([d] >> expr, [v2]))

        self.assertUnificationResult(e1, e2, expectedResult)
