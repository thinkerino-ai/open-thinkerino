from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

from aitools.logic import Substitution, Expression


class Prover:
    def __call__(self, formula: Expression, kb=None):
        raise NotImplementedError


@dataclass(frozen=True)
class ProofStep:
    inference_rule: Prover
    conclusion: Expression
    substitution: Substitution
    premises: Iterable[ProofStep] = None
