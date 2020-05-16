from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Union, Collection, Any

from aitools.logic import Substitution, Expression, LogicObject
from aitools.logic.utils import normalize_variables
from aitools.proofs.components import Component, HandlerSafety
from aitools.proofs import context
from aitools.proofs.exceptions import UnsafeOperationException


@dataclass
class TruthSubstitution:
    truth: bool
    substitution: Substitution


@dataclass
class TruthSubstitutionPremises:
    truth: bool
    substitution: Substitution
    premises: Union[Proof, Collection[Proof]]


class Prover(Component):
    def prove(self, formula: LogicObject, *, previous_substitution: Substitution) -> Iterable[Proof]:
        if context.is_hypothetical_scenario() and self.safety == HandlerSafety.TOTALLY_UNSAFE:
            raise UnsafeOperationException("Unsafe listener cannot be used in hypothetical scenarios")

        normalized_listened_formula, normalization_mapping = normalize_variables(self.listened_formula)
        unifier = Substitution.unify(formula, normalized_listened_formula, previous=previous_substitution)

        if unifier is None:
            return

        try:
            args_by_name = self._extract_args_by_name(formula, unifier, normalization_mapping=normalization_mapping)
        except ValueError:
            return

        result = self.handler(**args_by_name)

        if result is None:
            return

        # if the handler returned a single value, wrap it in a tuple to make it iterable
        if (
                isinstance(result, (Substitution, TruthSubstitution, TruthSubstitutionPremises)) or
                # the result is a pair or a triple, but not "made of results
                (
                        isinstance(result, tuple) and
                        len(result) in (2, 3) and
                        not all(isinstance(x, Substitution) for x in result)
                )
        ):
            result = (result,)

        for item in result:
            if isinstance(item, tuple):
                if len(item) == 2:
                    truth, substitution = item
                    premises = ()
                elif len(item) == 3:
                    truth, substitution, premises = item
                    # again, if a single proof was returned, we wrap it in a tuple to make it iterable
                    if isinstance(premises, Proof):
                        premises = (premises,)
                else:
                    raise ValueError("A handler returned tuple must have length 2 or 3")
            elif isinstance(item, bool):
                truth = item
                substitution = unifier
                premises = ()
            elif isinstance(item, Substitution):
                truth = True
                substitution = item
                premises = ()
            elif isinstance(item, TruthSubstitution):
                truth = item.truth
                substitution = item.substitution
                premises = ()
            elif isinstance(item, TruthSubstitutionPremises):
                truth = item.truth
                substitution = item.substitution
                premises = (item.premises,) if isinstance(item.premises, Proof) else item.premises
            else:
                raise ValueError(
                    f"A Prover's handler cannot return a {type(item)}, read the docs! Substitutions, booleans, "
                    f"(boolean, substitution) pairs, (boolean, substitution, Proof/Proofs) triples, "
                    f"TruthSubstitution instances or TruthSubstitutionPremises instances! "
                    f"What is a {type(item)}????"
                )

            if truth:
                proof = Proof(
                    inference_rule=self,
                    conclusion=substitution.apply_to(formula),
                    substitution=substitution,
                    premises=tuple(premises)
                )

                yield proof


@dataclass(frozen=True)
class Proof:
    # TODO inference_rule should be a Verifier or something
    inference_rule: Any
    conclusion: Expression
    substitution: Substitution
    premises: Iterable[Proof] = ()
