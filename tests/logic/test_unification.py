import unittest
from typing import Optional

import pytest

from aitools.logic import Substitution, Variable, LogicObject, Binding, UnificationError
from aitools.logic.utils import constants, expr, variables, subst, binding, wrap


class TestUnification(unittest.TestCase):

    def assertUnificationResult(self, e1: LogicObject, e2: LogicObject, expected_result: Optional[Substitution], *,
                                previous: Substitution = None):
        result = Substitution.unify(e1, e2, previous=previous)
        if expected_result is not None:
            self.assertIsNotNone(result)
        self.assertEqual(result, expected_result,
                         f"Unification between {e1} and {e2} should give {expected_result}, got {result} instead")

    def testBindingJoin(self):
        x, y, z = variables('x, y, z')
        a, b = constants('a, b')

        h1 = expr(z)
        h2 = expr(b)

        b1 = Binding(frozenset([x]), h1)
        b2 = Binding(frozenset([y]), h2)

        try:
            assert Binding.join(b1, b2).head == h2
        except UnificationError as e:
            pytest.fail(str(e))

    def testUnificationBetweenLogicObjectsFailure(self):
        a, b = constants('a, b')

        self.assertUnificationResult(a, b, None)

    def testUnificationBetweenLogicObjectsSuccess(self):
        a, = constants('a')

        expected_result = subst()
        self.assertUnificationResult(a, a, expected_result)

    def testUnificationBetweenExpressionsSuccess(self):
        a, b, c, d = constants('a, b, c, d')
        e1 = expr(a, (b, c), d)
        e2 = expr(a, (b, c), d)

        expected_result = subst()
        self.assertUnificationResult(e1, e2, expected_result)

    def testUnificationBetweenExpressionsFailure(self):
        a, b, c, d = constants('a, b, c, d')
        e1 = expr(a, (b, c), d)
        e2 = expr(a, (b, c), a)

        self.assertUnificationResult(e1, e2, None)

    def testUnificationWithVariablesSuccessSimple(self):
        v1, = variables('v1')
        a, b, c, d = constants('a, b, c, d')

        expr_d = expr([d])
        e1 = expr(a, (b, c), expr_d)

        expected_result = subst((e1, [v1]))

        self.assertUnificationResult(v1, e1, expected_result)

    def testUnificationWithVariablesSuccessComplex(self):
        v1, v2 = variables('v1, v2')
        a, b, c, d = constants('a, b, c, d')

        expr_d = expr([d])
        e1 = expr(a, (b, c), expr_d)
        e2 = expr(a, (v1, c), v2)

        expected_result = subst((b, [v1]), (expr_d, [v2]))

        self.assertUnificationResult(e1, e2, expected_result)

    def testUnificationWithVariablesFailureConflict(self):
        v1, = variables('v1')
        a, b, c, d = constants('a, b, c, d ')

        expr_d = expr([d])
        e1 = expr(a, (b, c), expr_d)
        e3 = expr(a, (v1, c), v1)

        self.assertUnificationResult(e1, e3, None)

    def testUnificationWithVariablesSuccessEquality(self):
        v1, v2 = variables('v1, v2')
        a, c = constants('a, c')

        e2 = expr(a, (v1, c), v2)
        e3 = expr(a, (v1, c), v1)

        expected_result = subst((None, [v1, v2]))

        self.assertUnificationResult(e2, e3, expected_result)

    def testUnificationWithVariablesFailureContained(self):
        v1, v2 = variables('v1, v2')
        a, c, d = constants('a, c, d')

        expr_d = expr([d])
        e2 = expr(a, (v1, c), v2)
        e4 = expr(a, v1, expr_d)

        self.assertUnificationResult(e2, e4, None)

    def testUnificationWithVariablesSuccessSameExpression(self):
        v1, v2 = variables('v1, v2')
        a, b, c, d = constants('a, b, c, d')

        bc_expr1 = expr(b, c)
        bc_expr2 = expr(b, c)
        e1 = expr(a, bc_expr1, v1, d)
        e2 = expr(a, v2, bc_expr2, d)

        expected_result = subst((bc_expr1, [v1]), (bc_expr2, [v2]))

        self.assertUnificationResult(e1, e2, expected_result)

    def testUnificationWithPreviousSimpleSucceeding(self):
        x = Variable(name='x')
        a, b, c, d = constants('a, b, c, d')

        bc_expr = expr(b, c)
        e1 = expr(a, bc_expr, d)
        e2 = expr(a, x, d)

        previous = subst((bc_expr, [x]))

        self.assertUnificationResult(e1, e2, previous, previous=previous)

    def testUnificationWithPreviousSimpleFailing(self):
        x = Variable(name='x')
        a, b, c, d = constants('a, b, c, d')

        bc_expr = expr(b, c)
        e1 = expr(a, bc_expr, d)
        e2 = expr(a, x, d)

        previous = subst((b, [x]))

        self.assertUnificationResult(e1, e2, None, previous=previous)

    def testUnificationWithPreviousSuccessBoundToSameExpression(self):
        x, y, z = variables('x, y, z')
        a, d = constants('a, d')

        e2 = expr(a, x, z)
        e3 = expr(a, y, d)

        previous = subst((a, [x]), (a, [y]))

        expected_result = previous.with_bindings(binding(d, [z]))

        self.assertUnificationResult(e2, e3, expected_result, previous=previous)

    def testUnificationWithPreviousSuccessBoundToUnifiableExpressions(self):
        x, y, z = variables('x, y, z')
        a, b, c, d = constants('a, b, c, d')

        bc_expr = expr(b, c)
        bz_expr = expr(b, z)
        e2 = expr(a, x, d)
        e3 = expr(a, y, d)

        previous = subst((bc_expr, [x]), (bz_expr, [y]))

        expected_result = previous.with_bindings(binding(c, [z]))

        self.assertUnificationResult(e2, e3, expected_result, previous=previous)

    def testUnificationWithPreviousFailureBoundToDifferentExpressions(self):
        x, y = variables('x, y')
        a, b, d = constants('a, b, d')

        e2 = expr(a, x, d)
        e3 = expr(a, y, d)

        previous = subst((a, [x]), (b, [y]))

        self.assertUnificationResult(e2, e3, None, previous=previous)

    def testUnificationWithPrevious(self):
        w, x, y, z = variables('w, x, y, z')
        a, d = constants('a, d')

        e2 = expr(a, x, d)
        e3 = expr(a, y, d)

        previous = subst((None, [x, z]), (None, [y, w]))

        expected_result = subst((None, [w, x, y, z]))

        self.assertUnificationResult(e2, e3, expected_result, previous=previous)

    def testUnificationWithRepeatedConstants(self):
        v1 = Variable(name='x')

        e1 = expr(2, v1)
        e2 = expr(2, "hi")

        expected_result = subst((wrap("hi"), [v1]))
        self.assertUnificationResult(e1, e2, expected_result)

    def testUnificationWeirdFailingCase(self):
        v1, v2 = variables('v1, v2')
        c, d = constants('c, d')
        e1 = expr("hello", ("yay", c), [d])
        e2 = expr("hello", (v1, c), v2)

        expected_result = subst((wrap("yay"), [v1]), (expr([d]), [v2]))

        self.assertUnificationResult(e1, e2, expected_result)
