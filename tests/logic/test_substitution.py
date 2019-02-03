import unittest

from aitools.logic.utils import variables, logicObjects, subst, expr


class TestSubstitution(unittest.TestCase):

    def testComplexSubstitution(self):
        x, y, z = variables(3)
        a, b, c, d = logicObjects(4)

        e = (x, a) >> expr

        yExpr = (a, (b, y), d) >> expr
        zExpr = (c, z) >> expr

        s = subst((zExpr, [y]), (c, [z]), (yExpr, [x]))

        expectedResult = ((a, (b, (c, c)), d), a) >> expr

        self.assertEqual(s.applyTo(e), expectedResult)

    def testInfiniteSubstitution(self):
        x, = variables(1)
        a, = logicObjects(1)

        e = (x, a) >> expr

        try:
            s = subst((e, [x]))
            s.applyTo(e)
        except ValueError:
            pass  # success
        except RecursionError:
            self.fail("Infinite substitution happened")

    def testGetBoundObject(self):
        x, y = variables(2)

        a, b, c, d = logicObjects(4)

        e = (a, (b, c), d) >> expr

        s = subst((e, [x, y]))

        self.assertEqual(e, s.getBoundObjectFor(x))
        self.assertEqual(e, s.getBoundObjectFor(y))

    def testGetBoundVariable(self):
        x, y = variables(2)

        s = subst((None, [x,y]))

        self.assertEqual(s.getBoundObjectFor(x), s.getBoundObjectFor(y))
        self.assertTrue(s.getBoundObjectFor(x) in [x,y])
        self.assertTrue(s.getBoundObjectFor(y) in [x,y])