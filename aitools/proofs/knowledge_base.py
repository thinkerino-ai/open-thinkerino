import itertools
import logging
import typing
from collections import deque
from contextlib import contextmanager
from typing import Iterable

from aitools.logic import Expression, Substitution, LogicObject
from aitools.logic.utils import normalize_variables, VariableSource
from aitools.proofs.context import contextual
from aitools.proofs.listeners import Listener, PonderMode, TriggeringFormula
from aitools.proofs.provers import OLD_Prover, ProofSet, Proof
from aitools.proofs.builtin_provers import KnowledgeRetriever, RestrictedModusPonens
from aitools.proofs.utils import EmbeddedProver
from aitools.storage.base import LogicObjectStorage
from aitools.storage.implementations.dummy import DummyAbstruseIndex
from aitools.storage.index import AbstruseIndex, make_key

logger = logging.getLogger(__name__)


class KnowledgeBase:

    def __init__(self, storage: LogicObjectStorage):
        self._storage = storage
        self._variable_source = VariableSource()
        self._provers: typing.Set[OLD_Prover] = set()
        self._listener_storage: AbstruseIndex[Listener] = DummyAbstruseIndex()
        self.knowledge_retriever: OLD_Prover = KnowledgeRetriever()
        self._initialize_default_provers()

    def supports_transactions(self) -> bool:
        return self._storage.supports_transactions()

    @contextmanager
    def transaction(self):
        with self._storage.transaction():
            yield

    def commit(self):
        self._storage.commit()

    def rollback(self):
        self._storage.rollback()

    def _initialize_default_provers(self):
        # TODO although it's quite a standard proving strategy, I really don't like having MP as a default...
        self.add_provers(RestrictedModusPonens())

    def _retrieve(self, formula: Expression, *,
                  previous_substitution: Substitution = None) -> Iterable[Substitution]:
        """Retrieves all formula from the KnowledgeBase which are unifiable with the given one.
        No proofs are searched, so either a formula is **IN** the KB, or nothing will be returned."""
        # TODO here I am performing unification twice! I need to optimize this
        for expr, _ in self._storage.search_unifiable(other=formula):
            subst = Substitution.unify(
                normalize_variables(expr), formula,
                previous=previous_substitution
            )

            if subst is not None:
                yield subst

    def add_formulas(self, *formulas: Expression):
        """Adds all of the given formulas to the currently known formulas."""
        formulas = tuple(normalize_variables(f, variable_source=self._variable_source) for f in formulas)

        self._storage.add(*formulas)

    def add_provers(self, *provers):
        for p in provers:
            if isinstance(p, OLD_Prover):
                self._add_prover(p)
            else:
                self._add_prover(EmbeddedProver(p.wrapped_function, p.formula))

    def _add_prover(self, prover):
        self._provers.add(prover)

    def add_listener(self, listener: Listener):
        key = make_key(listener.listened_formula)
        self._listener_storage.add(key, listener)

    def __len__(self):
        return len(self._storage)

    # TODO 'formula' shouldn't be an Expression, because I could be trying to "prove a variable" (is this true? o.o I'm so sleepy)
    def prove(self, formula: Expression, *, retrieve_only: bool = False, truth: bool = True,
              previous_substitution=None) -> ProofSet:
        """Backward search to prove a given formulas using all known provers"""
        logger.info("Trying to prove %s to be %s with previous substitution %s", formula, truth, previous_substitution)

        previous_substitution = previous_substitution or Substitution()

        proof_sources: typing.Deque[Iterable[Proof]] = deque()
        proof_sources.append(
            self.knowledge_retriever(formula, _kb=self, _truth=truth, _previous_substitution=previous_substitution)
        )

        if not retrieve_only:
            proof_sources.extend(
                prover(formula, _kb=self, _truth=truth, _previous_substitution=previous_substitution)
                for prover in self._provers
            )

            _embedded_prover: OLD_Prover = getattr(formula, '_embedded_prover', None)
            if _embedded_prover is not None:
                proof_sources.appendleft(_embedded_prover(formula=formula, _kb=self, _truth=truth))

        @contextual('kb', self)
        def _inner():
            while any(proof_sources):
                source = proof_sources.popleft().__iter__()
                logger.debug("Trying to prove %s with %s", formula, source)
                try:
                    new_proof = next(source)
                    logger.debug("Found a proof...")
                except StopIteration:
                    pass
                else:
                    proof_sources.append(source)
                    yield new_proof

        return ProofSet(_inner())

    def ponder(self, *formulas: Iterable[LogicObject], ponder_mode: PonderMode):
        @contextual('kb', self)
        def _inner():
            input_sources: deque[Iterable[Proof]] = deque(
                self._preprocess_pondering_inputs(formulas, ponder_mode)
            )

            pondering_processes: deque[Iterable[Proof]] = deque()

            while len(input_sources) > 0 or len(pondering_processes) > 0:
                # one step on input_processes, to produce more pondering_processes (if necessary)
                if len(input_sources) > 0:
                    first_source_iterable = input_sources.popleft()
                    input_source = first_source_iterable.__iter__()
                    try:
                        new_input: Proof = next(input_source)
                    except StopIteration:
                        pass
                    else:
                        for listener in self.get_listeners_for(new_input.conclusion):
                            trigger_premise = Proof(
                                inference_rule=TriggeringFormula(),
                                conclusion=new_input.substitution.apply_to(new_input.conclusion),
                                substitution=new_input.substitution,
                                premises=(new_input,)
                            )
                            pondering_processes.append(listener.ponder(trigger_premise))
                        input_sources.append(input_source)

                # one step on pondering_processes, to produce results (and more input_processes)
                if len(pondering_processes) > 0:
                    pondering_process = pondering_processes.popleft().__iter__()
                    try:
                        new_listener_proof: Proof = next(pondering_process)
                    except StopIteration:
                        pass
                    else:
                        input_sources.append((new_listener_proof,))
                        pondering_processes.append(pondering_process)
                        yield new_listener_proof

        yield from _inner()

    def _preprocess_pondering_inputs(self, formulas, ponder_mode) -> Iterable[Iterable[Proof]]:
        if ponder_mode == PonderMode.HYPOTHETICALLY:
            raise NotImplementedError("This case requires hypotheses to be implemented :P")
        elif ponder_mode == PonderMode.KNOWN:
            input_sources = (
                (lambda f: self.prove(f, retrieve_only=True))(formula)
                for formula in formulas
            )
        elif ponder_mode == PonderMode.PROVE:
            input_sources = (
                (lambda f: self.prove(f))(formula)
                for formula in formulas
            )
        else:
            raise NotImplementedError(f"Unknown ponder mode: {ponder_mode}")
        return input_sources

    def get_listeners_for(self, formula):
        key = make_key(formula)
        yield from self._listener_storage.retrieve(key)