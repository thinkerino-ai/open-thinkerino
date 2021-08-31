import unittest

from aitools.logic.core import Variable, Constant
from aitools.logic.language import Language
from aitools.logic.utils import variables, constants, subst, expr


class TestSubstitution(unittest.TestCase):

    def testComplexSubstitution(self):
        language = Language()
        x, y, z = variables('x, y, z', language=language)
        a, b, c, d = constants('a, b, c, d', language=language)

        e = expr(x, a)

        y_expr = expr(a, (b, y), d)
        z_expr = expr(c, z)

        s = subst((z_expr, [y]), (c, [z]), (y_expr, [x]))

        expected_result = expr((a, (b, (c, c)), d), a)

        self.assertEqual(s.apply_to(e), expected_result)

    def testInfiniteSubstitution(self):
        language = Language()
        x = Variable(name='x', language=language)
        a = Constant(name='a', language=language)

        e = expr(x, a)

        try:
            # TODO pytest.raises :P
            s = subst((e, [x]))
            s.apply_to(e)
        except ValueError:
            pass  # success
        except RecursionError:
            self.fail("Infinite substitution happened")

    def testGetBoundObject(self):
        language = Language()
        x, y = variables('x, y', language=language)

        a, b, c, d = constants('a, b, c, d', language=language)

        e = expr(a, (b, c), d)

        s = subst((e, [x, y]))

        self.assertEqual(e, s.get_bound_object_for(x))
        self.assertEqual(e, s.get_bound_object_for(y))

    def testGetBoundVariable(self):
        language = Language()
        x, y = variables(2, language=language)

        s = subst((None, [x, y]))

        self.assertEqual(s.get_bound_object_for(x), s.get_bound_object_for(y))
        self.assertTrue(s.get_bound_object_for(x) in [x, y])
        self.assertTrue(s.get_bound_object_for(y) in [x, y])

    def test_tricky_substitution(self):
        language = Language()
        x, y, z = variables('x, y, z', language=language)
        a, b, c = constants('a, b, c ', language=language)

        s = subst((b, [y]), (a(y), [x]))

        expected = a(b)

        self.assertEqual(expected, s.apply_to(x))
