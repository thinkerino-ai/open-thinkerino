from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

from aitools.logic import Substitution
from aitools.proofs.language import Formula


class Prover:
    def __call__(self, formula: Formula, kb=None):
        raise NotImplementedError


@dataclass(frozen=True)
class ProofStep:
    inference_rule: Prover
    conclusion: Formula
    substitution: Substitution
    premises: Iterable[ProofStep] = None
