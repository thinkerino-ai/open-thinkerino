from aitools.proofs.language import Formula, Implies
from aitools.proofs.proof import Prover, ProofStep
from aitools.logic.utils import variable_source as v


class KnowledgeRetriever(Prover):

    def __call__(self, formula: Formula, kb=None):
        for subst in kb.retrieve(formula):
            yield ProofStep(inference_rule=self, conclusion=formula, substitution=subst)


class RestrictedModusPonens(Prover):
    """Restricted backward version of modus ponens, which won't perform recursive proof of implications"""
    def __call__(self, formula: Formula, kb=None):
        if not formula.children[0] == Implies:
            rule_pattern = Implies(v._premise, formula)

            for rule_proof in kb.prove(rule_pattern):
                premise = rule_proof.substitution.getBoundObjectFor(v._premise)
                for premise_proof in kb.prove(rule_proof.substitution.applyTo(premise)):
                    yield ProofStep(inference_rule=self, conclusion=formula, substitution=premise_proof.substitution,
                                    premises=(rule_proof, premise_proof))
