import unittest

from aitools.logic.utils import variables, logic_objects, subst, expr


class TestSubstitution(unittest.TestCase):

    def testComplexSubstitution(self):
        x, y, z = variables(3)
        a, b, c, d = logic_objects(4)

        e = expr(x, a)

        y_expr = expr(a, (b, y), d)
        z_expr = expr(c, z)

        s = subst((z_expr, [y]), (c, [z]), (y_expr, [x]))

        expected_result = expr((a, (b, (c, c)), d), a)

        self.assertEqual(s.apply_to(e), expected_result)

    def testInfiniteSubstitution(self):
        x, = variables(1)
        a, = logic_objects(1)

        e = expr(x, a)

        try:
            s = subst((e, [x]))
            s.apply_to(e)
        except ValueError:
            pass  # success
        except RecursionError:
            self.fail("Infinite substitution happened")

    def testGetBoundObject(self):
        x, y = variables(2)

        a, b, c, d = logic_objects(4)

        e = expr(a, (b, c), d)

        s = subst((e, [x, y]))

        self.assertEqual(e, s.get_bound_object_for(x))
        self.assertEqual(e, s.get_bound_object_for(y))

    def testGetBoundVariable(self):
        x, y = variables(2)

        s = subst((None, [x, y]))

        self.assertEqual(s.get_bound_object_for(x), s.get_bound_object_for(y))
        self.assertTrue(s.get_bound_object_for(x) in [x, y])
        self.assertTrue(s.get_bound_object_for(y) in [x, y])

    def test_tricky_substitution(self):
        x, y, z = variables(3)
        a, b, c = logic_objects(3)

        s = subst((b, [y]), (a(y), [x]))

        expected = a(b)

        self.assertEqual(expected, s.apply_to(x))
