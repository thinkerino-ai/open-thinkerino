# Ideas

- KnowledgeBase.prove:
    - returns a "proofset", which **can** be async
    - the proofset is in any case lazy
    - it exposes the __iter__ method
    - it exposes the __len__ method
- a prover can return:
    - True: the formula is proven to be True without any further substitution
    - False: the formula is proven to be False without any further substitution
    - None: the formula couldn't be proven either True or False by this prover
    - a Substitution: the formula was proven to be True with this Substitution
    - a sequence of Substitutions: the formula was proven to be True with all of the Substitutions
    - a pair `(bool, Substitution)`: the formula was proven to be True/False with the Substitution
    - a sequence of pairs: the formula was proven to be True/False with each of the Substitutions
    - **raise**: just like returning None
- `prover` decorator:
    - the `proves` argument can be either a Formula or a collection of Formula
    - it provides a default variable source to create the variables for the decorated function/generated predicate
        - the variable source can be provided by hand to override it
        - the default one is taken from the current (global) context
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

