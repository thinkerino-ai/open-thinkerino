# Ideas

- a proof must be **reproducible** by doing all of the following:
    - checking its premises (if any)
    - calling its inference step on the conclusion passing the premises as an "ad-hoc" KB
- KnowledgeBase.prove:
    - returns a "proofset", which **can** be async
    - the proofset is in any case lazy
    - it exposes the __iter__ method
    - it exposes the __len__ method
    - can take additional hypotheses and prove taking them in account (the good old A |- B)
    - takes a`truth` argument which specifies whether to search for proofs **for** the formula or **against** it (prove that it is false) 
- KnowledgeBase.with_hypotheses:
    - returns a new "temporary" knowledge base which contains all the hypotheses and has the original as a fallback
- a prover **function** can return:
    - True: the formula is proven to be True without any further substitution
    - False: the formula is proven to be False without any further substitution
    - None: the formula couldn't be proven either True or False by this prover
    - a Substitution: the formula was proven to be True with this Substitution
    - a sequence of Substitutions: the formula was proven to be True with all of the Substitutions
    - a pair `(bool, Substitution)`: the formula was proven to be True/False with the Substitution
    - a sequence of pairs: the formula was proven to be True/False with each of the Substitutions
    - **raise**: just like returning None
    - a Proof
    - a sequence of Proofs
- `prover` decorator:
    - the `proves` argument can be either a Formula ~~or a collection of Formula (makes no sense!)~~
    - it provides a default variable source to create the variables for the decorated function/generated predicate
        - the variable source can be provided by hand to override it
        - the default one is taken from the current (global) context
    - when called it takes optional "kb" kwarg, which specifies what to base the proof on, including hypotheses
    - returns a sequence of proofs
    - if the decorated function returned boolean/Subsitution/pair or a sequence of these, it creates an *implicit proof*
        - built on the proofs requested by the decorated function (and their result)
            - this can lead to a very large premise set (depending on the complexity of the prover)
            - it also **needs to account for "python" checks** (i.e. flow control based on anything except proofs), by including a special term representing the prover
                - an optional "is_transparent" argument to the `@prover` decorator prevents this
        - the decorated function can also use a `with premises(...)` before returning or yielding, which overrides the implicit premises (and also behaves as if `is_transparent` was set for the returned result)
- an evaluator is like a prover, but it returns an object which is the evaluation of the input
    - this can lead to cycles! we need to avoid them!
- listeners (aka: forward provers):
    - they can listen for one or more formulas (in conjunction)
    - they can be passed to a KnowledgeBase, but also to a CognitiveSystem (the 'mind', the KB is actually given to it)
        - they have an 'owner', 
    - applying more than one allows for disjunction (each @listener listens independently from the others, even on the same function)
    - a KnowledgeBase is just a @listener given to the CognitiveSystem
    - listeners have priorities which influence the order in which they are evaluated (positive integers)
    - listeners can be "partially activated", which generates temporary listeners
        - there can be only so many temporary listeners
        - which temporary listener to kill is determined by:
            - the priority (usually inherited from the listener)
            - the age function (**keyword param for @listener** with a default which uses the one from its 'owner' or from the parent)
                - if the age function is order-preserving, we don't need to sort the listeners at every "update"
                - otherwise we do! :(
    
-----

## Pile-of-stuff

### Hybrid Chains

Here I'd like to chain somehow provers and formulas, but I'm too tired to even know what I mean :P
Since it's not fundamental (or, more specifically, I'm mostly confident it'll work when everything else does), I'll leave it here.

```python
def test_chain_multiple_results():
    @prover
    def HasKey(obj, key):
        if isinstance(key, Variable):
            for el in obj:
                yield subst(el, [_x])
        else:
            yield True

    kb = KnowledgeBase()

    kb.add_provers(HasKey)

    kb.add_formulas(HasKey(v._obj, v._key) >> ?)
```

