from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from aitools.logic import Substitution, Expression


class Prover:
    def __call__(self, formula: Expression, _kb=None, _truth: bool = True,
                 _previous_substitution: Substitution = None) -> Iterable[Proof]:
        raise NotImplementedError


@dataclass(frozen=True)
class Premise:
    premise: Expression
    source: Proof = None


@dataclass(frozen=True)
class Proof:
    inference_rule: Prover
    conclusion: Expression
    substitution: Substitution
    premises: Iterable[Premise] = ()


class ProofSet:
    def __init__(self, proofs: Iterable[Proof]):
        self._proofs = proofs

    def __iter__(self):
        yield from self._proofs

    def __bool__(self):
        return any(self._proofs)
