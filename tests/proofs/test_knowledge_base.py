import pytest

from aitools.logic import Expression, LogicObject
from aitools.proofs.knowledge_base import KnowledgeBase
from aitools.proofs.language import Formula


def test_only_formulas_can_be_added():
    kb = KnowledgeBase()

    with pytest.raises(TypeError):
        kb.add_formulas(Expression(LogicObject()))

    kb.add_formulas(Formula(LogicObject()))
