import unittest

from aitools.logic import LogicWrapper, Variable, Constant, Expression
from aitools.logic.utils import expr, wrap


class TestLogicWrappers(unittest.TestCase):

    def testStringConstantInDSL(self):
        v1 = Variable()
        a = Constant()

        e = expr(v1, a, "hello")

        self.assertIsInstance(e.children[0], Variable, f"{e.children[0]} should be a Variable")
        self.assertIsInstance(e.children[1], Constant, f"{e.children[1]} should be a Constant")
        self.assertIsInstance(e.children[2], LogicWrapper, f"{e.children[2]} should be a LogicWrapper")

    def testArrayConstantInDSL(self):
        src = ["hello", 2]
        e1 = expr(src)

        self.assertIsInstance(e1, Expression, f"{e1} should be an Expression!")
        self.assertEqual(len(e1.children), len(src), f"Length of {e1.children} and {src} should be equal!")
        for c in e1.children:
            self.assertIsInstance(c, LogicWrapper, f"{c} should be a LogicWrapper")

    def testWrappedArrayConstantInDSL(self):
        src = ["hello", 2]
        e1 = expr(wrap(src))

        self.assertIsInstance(e1, LogicWrapper, f"{e1} should be a LogicWrapper!")
        self.assertEqual(e1.value, src, f"The value of {e1} should be {src}")

    def testUtilsWrapSet(self):
        src1 = {1, 2, 3}
        src2 = [1, 2, 3]

        e1 = expr(src1, src2)
        
        # sets are wrapped, lists are mapped
        self.assertIsInstance(e1.children[0], LogicWrapper)
        self.assertIsInstance(e1.children[1], Expression)

        # the first element is just a wrapper around src1
        self.assertEqual(e1.children[0], wrap(src1))

        # the second element is a list of wrappers
        self.assertEqual(e1.children[1].children, tuple(map(wrap, src2)))

    def test_magic_methods(self):
        assert (LogicWrapper(5) + LogicWrapper(2)) == (5 + 2)
        assert (LogicWrapper(5) - LogicWrapper(2)) == (5 - 2)
        assert (LogicWrapper(5) * LogicWrapper(2)) == (5 * 2)
        assert (LogicWrapper(5) / LogicWrapper(2)) == (5 / 2)
        assert (LogicWrapper(5) // LogicWrapper(2)) == (5 // 2)
        assert (LogicWrapper(5) % LogicWrapper(2)) == (5 % 2)
        assert (LogicWrapper(5) ** LogicWrapper(2)) == (5 ** 2)
        assert (LogicWrapper(5) >> LogicWrapper(2)) == (5 >> 2)
        assert (LogicWrapper(5) << LogicWrapper(2)) == (5 << 2)
        assert (LogicWrapper(5) & LogicWrapper(2)) == (5 & 2)
        assert (LogicWrapper(5) | LogicWrapper(2)) == (5 | 2)
        assert (LogicWrapper(5) ^ LogicWrapper(2)) == (5 ^ 2)
        assert (LogicWrapper(5) < LogicWrapper(2)) == (5 < 2)
        assert (LogicWrapper(5) > LogicWrapper(2)) == (5 > 2)
        assert (LogicWrapper(5) <= LogicWrapper(2)) == (5 <= 2)
        assert (LogicWrapper(5) >= LogicWrapper(2)) == (5 >= 2)

        assert (LogicWrapper(5) + 2) == (5 + 2)
        assert (LogicWrapper(5) - 2) == (5 - 2)
        assert (LogicWrapper(5) * 2) == (5 * 2)
        assert (LogicWrapper(5) / 2) == (5 / 2)
        assert (LogicWrapper(5) // 2) == (5 // 2)
        assert (LogicWrapper(5) % 2) == (5 % 2)
        assert (LogicWrapper(5) ** 2) == (5 ** 2)
        assert (LogicWrapper(5) >> 2) == (5 >> 2)
        assert (LogicWrapper(5) << 2) == (5 << 2)
        assert (LogicWrapper(5) & 2) == (5 & 2)
        assert (LogicWrapper(5) | 2) == (5 | 2)
        assert (LogicWrapper(5) ^ 2) == (5 ^ 2)
        assert (LogicWrapper(5) < 2) == (5 < 2)
        assert (LogicWrapper(5) > 2) == (5 > 2)
        assert (LogicWrapper(5) <= 2) == (5 <= 2)
        assert (LogicWrapper(5) >= 2) == (5 >= 2)

        assert (5 + LogicWrapper(2)) == (5 + 2)
        assert (5 - LogicWrapper(2)) == (5 - 2)
        assert (5 * LogicWrapper(2)) == (5 * 2)
        assert (5 / LogicWrapper(2)) == (5 / 2)
        assert (5 // LogicWrapper(2)) == (5 // 2)
        assert (5 % LogicWrapper(2)) == (5 % 2)
        assert (5 ** LogicWrapper(2)) == (5 ** 2)
        assert (5 >> LogicWrapper(2)) == (5 >> 2)
        assert (5 << LogicWrapper(2)) == (5 << 2)
        assert (5 & LogicWrapper(2)) == (5 & 2)
        assert (5 | LogicWrapper(2)) == (5 | 2)
        assert (5 ^ LogicWrapper(2)) == (5 ^ 2)
        assert (5 < LogicWrapper(2)) == (5 < 2)
        assert (5 > LogicWrapper(2)) == (5 > 2)
        assert (5 <= LogicWrapper(2)) == (5 <= 2)
        assert (5 >= LogicWrapper(2)) == (5 >= 2)