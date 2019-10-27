import logging
import typing
import abc
from collections import deque
from typing import Set, Collection, Optional, Iterable

from aitools.logic import Expression, Substitution
from aitools.logic.utils import normalize_variables, VariableSource
from aitools.proofs.context import contextual
from aitools.proofs.listeners import Listener, _MultiListenerWrapper
from aitools.proofs.proof import Prover, ProofSet, Proof
from aitools.proofs.provers import KnowledgeRetriever, RestrictedModusPonens
from aitools.proofs.utils import EmbeddedProver

logger = logging.getLogger(__name__)


class KnowledgeBase(metaclass=abc.ABCMeta):

    def __init__(self):
        self._initialize_default_provers()

    @property
    @abc.abstractmethod
    def _variable_source(self):
        raise NotImplementedError()

    def _initialize_default_provers(self):
        self.add_provers(KnowledgeRetriever())
        # although it's quite a standard proving strategy, I really don't like having MP as a default...
        self.add_provers(RestrictedModusPonens())

    @abc.abstractmethod
    def retrieve(self, formula: Optional[Expression] = None, *, previous_substitution: Substitution = None) -> Iterable[Substitution]:
        """Retrieves all formula from the KnowledgeBase which are unifiable with the given one.
        No proofs are searched, so either a formula is **IN** the KB, or nothing will be returned."""
        raise NotImplementedError()

    def add_formulas(self, *formulas: Expression):
        """Adds all of the given formulas to the currently known formulas."""
        formulas = tuple(normalize_variables(f, variable_source=self._variable_source) for f in formulas)

        self._add_formulas(*formulas)

        for f in formulas:
            self._on_formula_proven(f)

    @abc.abstractmethod
    def _add_formulas(self, *formulas: Expression):
        raise NotImplementedError()

    def add_provers(self, *provers):
        for p in provers:
            if isinstance(p, Prover):
                self._add_prover(p)
            else:
                self._add_prover(EmbeddedProver(p.wrapped_function, p.formula))

    @abc.abstractmethod
    def _add_prover(self, prover):
        raise NotImplementedError()

    def add_listeners(self, *listeners: typing.Union[Listener, _MultiListenerWrapper],
                      retroactive: bool = False, temporary=False):
        if retroactive:
            raise NotImplementedError("Not implemented yet!")

        for el in listeners:
            if isinstance(el, Listener):
                self._add_listener(el, retroactive=retroactive, temporary=temporary)
            elif isinstance(el, _MultiListenerWrapper):
                for l in el.listeners:
                    self._add_listener(l, retroactive=retroactive, temporary=temporary)

    @abc.abstractmethod
    def _add_listener(self, listener: Listener, retroactive: bool = False, temporary=False):
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def _provers(self):
        raise NotImplementedError()

    # TODO 'formula' shouldn't be an Expression, because I could be trying to "prove a variable" (is this true? o.o I'm so sleepy)
    def prove(self, formula: Expression, truth: bool = True, previous_substitution = None) -> ProofSet:
        """Backward search to prove a given formulas using all known provers"""
        logger.info("Trying to prove %s to be %s with previous substitution %s", formula, truth, previous_substitution)

        previous_substitution = previous_substitution or Substitution()

        proof_sources: typing.Deque[Iterable[Proof]] = deque(
            prover(formula, _kb=self, _truth=truth, _previous_substitution=previous_substitution)
            for prover in self._provers
        )

        _embedded_prover: Prover = getattr(formula, '_embedded_prover', None)
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
                    self._on_formula_proven(new_proof.substitution.apply_to(new_proof.conclusion))
                    yield new_proof

        return ProofSet(_inner())

    def _on_formula_proven(self, formula):
        for listener in self._get_listeners_for(formula):
            self._process_listener(listener, formula)

        for listener in self._get_listeners_for(formula, temporary=True):
            self._process_listener(listener, formula)

    def _process_listener(self, listener, formula):
        raw_output = listener.extract_and_call(formula)
        if raw_output is None:
            return

        output = (raw_output,) if isinstance(raw_output, (Expression, Listener, _MultiListenerWrapper)) \
            else raw_output

        # TODO it would help to keep these separated from the actual formulas, to prevent overflowing memory
        for obj in output:
            if isinstance(obj, Expression):
                self.add_formulas(obj)
            elif isinstance(obj, Listener):
                self.add_listeners(obj, temporary=True)
            elif isinstance(obj, _MultiListenerWrapper):
                self.add_listeners(*obj.listeners, temporary=True)

    @abc.abstractmethod
    def _get_listeners_for(self, formula: Expression, *, temporary=False):
        raise NotImplementedError()

    @abc.abstractmethod
    def __len__(self):
        raise NotImplementedError()
