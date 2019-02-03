import unittest

from aitools.logic import LogicObject, Variable
from aitools.logic.utils import expr


class TestLogicWrappers(unittest.TestCase):

    def testStringConstantInDSL(self):
        v1 = Variable()
        a = LogicObject()

        (v1, a, "ciao") >> expr
