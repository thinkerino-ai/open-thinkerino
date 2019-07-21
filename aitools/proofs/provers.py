from aitools.proofs.language import Formula, Implies
from aitools.proofs.proof import Prover, ProofStep
from aitools.logic.utils import variable_source as v


class KnowledgeRetriever(Prover):

    def __call__(self, formula: Formula, kb=None):
        for subst in kb.retrieve(formula):
            yield ProofStep(inference_rule=self, conclusion=formula, substitution=subst)


class RestrictedModusPonens(Prover):

    def __call__(self, formula: Formula, kb=None):
        rule_pattern = Implies(v._premise, formula)
        return iter([])
        for subst in self.__kb.retrieve(rule_pattern):
            premise = subst.getBoundObjectFor(v._premise)
            for premise_proof in self.__kb.prove(subst.applyTo(premise)):
                pass