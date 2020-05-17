import logging

from aitools.logic import Expression, Variable, Substitution
from aitools.logic.utils import VariableSource
from aitools.proofs.components import HandlerArgumentMode, HandlerSafety
from aitools.proofs.language import Implies, Not
from aitools.proofs.provers import TruthSubstitutionPremises, Prover, TruthSubstitution

logger = logging.getLogger(__name__)


def restricted_modus_ponens(formula, substitution, kb):
    """Restricted backward version of modus ponens, which won't perform recursive proof of implications"""
    v = VariableSource()
    if not (isinstance(formula, Expression) and formula.children[0] == Implies):
        rule_pattern = Implies(v.premise, formula)

        for rule_proof in kb.prove(rule_pattern, previous_substitution=substitution):
            premise = rule_proof.substitution.get_bound_object_for(v.premise)
            for premise_proof in kb.prove(premise, previous_substitution=rule_proof.substitution):
                yield TruthSubstitutionPremises(truth=True, substitution=premise_proof.substitution,
                                                premises=(rule_proof, premise_proof))


RestrictedModusPonens = Prover(
    listened_formula=Variable(), handler=restricted_modus_ponens, argument_mode=HandlerArgumentMode.RAW,
    pass_substitution_as=..., pass_knowledge_base_as='kb', pure=True, safety=HandlerSafety.SAFE
)


def closed_world_assumption(formula, substitution, kb):
    v = VariableSource()
    match = Substitution.unify(formula, Not(v.P))
    if match is not None:
        try:
            next(kb.prove(match.get_bound_object_for(v.P)))
        except StopIteration:
            return TruthSubstitution(True, substitution)


ClosedWorldAssumption = Prover(
    listened_formula=Variable(), handler=closed_world_assumption, argument_mode=HandlerArgumentMode.RAW,
    pass_substitution_as=..., pass_knowledge_base_as='kb', pure=True, safety=HandlerSafety.SAFE
)
