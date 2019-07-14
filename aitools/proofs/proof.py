from dataclasses import dataclass
from typing import Iterable, List

from aitools.logic import Expression, Substitution


class Prover:
    def __call__(self, formula: Expression):
        raise NotImplementedError


@dataclass(frozen=True)
class ProofStep:
    inference_rule: Prover
    conclusions: Iterable[Expression]
    substitution: Substitution


class Proof:
    def __init__(self, steps: Iterable[ProofStep]):
        if not steps:
            raise ValueError("A proof cannot be empty!")
        self.steps: List[ProofStep] = list(steps)
        self.conclusions = self.steps[-1].conclusions
        self.substitution = self.steps[-1].substitution

    def __len__(self):
        return len(self.steps)

    def __getitem__(self, item):
        return self.steps[item]

class KnowledgeRetriever(Prover):
    def __init__(self, knowledge_base):
        self.__knowledge_base = knowledge_base

    def __call__(self, formula: Expression):
        for subst in self.__knowledge_base.retrieve(formula):
            yield Proof(
                steps=[ProofStep(inference_rule=self, conclusions=[formula], substitution=subst)]
            )
