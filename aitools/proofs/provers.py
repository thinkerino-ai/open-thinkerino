from aitools.logic import Expression
from aitools.proofs.language import Implies
from aitools.proofs.proof import Prover, ProofStep
from aitools.logic.utils import variable_source as v


class KnowledgeRetriever(Prover):

    def __call__(self, formula: Expression, kb=None):
        for subst in kb.retrieve(formula):
            yield ProofStep(inference_rule=self, conclusion=formula, substitution=subst)


class RestrictedModusPonens(Prover):
    """Restricted backward version of modus ponens, which won't perform recursive proof of implications"""
    def __call__(self, formula: Expression, kb=None):
        if not formula.children[0] == Implies:
            rule_pattern = Implies(v._premise, formula)

            for rule_proof in kb.prove(rule_pattern):
                premise = rule_proof.substitution.get_bound_object_for(v._premise)
                for premise_proof in kb.prove(rule_proof.substitution.apply_to(premise)):
                    yield ProofStep(inference_rule=self, conclusion=formula, substitution=premise_proof.substitution,
                                    premises=(rule_proof, premise_proof))
