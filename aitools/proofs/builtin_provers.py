import logging

from aitools.logic.core import Expression, Variable, LogicObject
from aitools.logic.unification import Substitution
from aitools.logic.utils import VariableSource
from aitools.proofs.components import HandlerArgumentMode, HandlerSafety
from aitools.proofs.knowledge_base import KnowledgeBase
from aitools.proofs.language import Implies, Not
from aitools.proofs.provers import TruthSubstitutionPremises, Prover, TruthSubstitution

logger = logging.getLogger(__name__)


async def restricted_modus_ponens(formula: LogicObject, substitution: Substitution, kb: KnowledgeBase):
    """Restricted backward version of modus ponens, which won't perform recursive proof of implications"""
    v = VariableSource()
    if not (isinstance(formula, Expression) and formula.children[0] == Implies):
        rule_pattern = Implies(v.premise, formula)

        async for rule_proof in kb.async_prove(rule_pattern, previous_substitution=substitution):
            premise = rule_proof.substitution.get_bound_object_for(v.premise)
            async for premise_proof in kb.async_prove(premise, previous_substitution=rule_proof.substitution):
                yield TruthSubstitutionPremises(truth=True, substitution=premise_proof.substitution,
                                                premises=(rule_proof, premise_proof))


RestrictedModusPonens = Prover(
    listened_formula=Variable(), handler=restricted_modus_ponens, argument_mode=HandlerArgumentMode.RAW,
    pass_substitution_as=..., pass_knowledge_base_as='kb', pure=True, safety=HandlerSafety.SAFE
)


async def closed_world_assumption(formula: LogicObject, substitution: Substitution, kb: KnowledgeBase):
    v = VariableSource()
    match = Substitution.unify(formula, Not(v.P))
    if match is not None:
        try:
            await kb.async_prove(match.get_bound_object_for(v.P)).__anext__()
        except StopAsyncIteration:
            return TruthSubstitution(True, substitution)


ClosedWorldAssumption = Prover(
    listened_formula=Variable(), handler=closed_world_assumption, argument_mode=HandlerArgumentMode.RAW,
    pass_substitution_as=..., pass_knowledge_base_as='kb', pure=True, safety=HandlerSafety.SAFE
)
