import unittest

from aitools.logic import LogicObject
from aitools.logic.utils import logic_objects, expr, binding, variables


class TestEquality(unittest.TestCase):

    def testExpressionEqualitySuccess(self):
        a, b, c, d = logic_objects(4)

        e1 = expr(a, (b, c), d)
        e2 = expr(a, (b, c), d)

        self.assertEqual(e1, e2, f"{e1} and {e2} should be equal!")

    def testExpressionEqualityFailure(self):
        a, b, c, d = logic_objects(4)

        e1 = expr(a, (b, c), d)
        e2 = expr(a, (b, c), a)

        self.assertNotEqual(e1, e2, f"{e1} and {e2} should not be equal!")

    def testBindingEqualitySuccessWithHead(self):
        a = LogicObject()

        v1, v2, v3 = variables(3)

        b1 = binding(a, [v1, v2, v3])
        b2 = binding(a, [v3, v2, v1])

        self.assertEqual(b1, b2)

    def testBindingEqualitySuccessWithoutHead(self):
        v1, v2, v3 = variables(3)

        b1 = binding(None, [v1, v2, v3])
        b2 = binding(None, [v2, v3, v1])

        self.assertEqual(b1, b2)

    def testBindingEqualityFailureVariables(self):
        a = LogicObject()

        v1, v2, v3 = variables(3)

        b1 = binding(a, [v1, v2, v3])
        b2 = binding(a, [v2, v1])

        self.assertNotEqual(b1, b2)

    def testBindingEqualityFailureHead(self):
        a, b = logic_objects(2)

        v1, v2 = variables(2)

        b1 = binding(a, [v1, v2])
        b2 = binding(b, [v2, v1])

        self.assertNotEqual(b1, b2)

    def testConstantsEquality(self):
        e1 = expr(2)
        e2 = expr(2)

        self.assertEqual(e1, e2)
