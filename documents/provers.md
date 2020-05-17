# Provers

The `KnowledgeBase.prove(...)` method tries to prove that **and how** a given formula is known to be "true" (more precisely: satisfiable).

For example, given "the right configuration", calling `prove(IsPrime(some_number))`, where `some_number` could be a `LogicWrapper` to an integer, could run some ad-hoc algorithm to perform the check.

On the other hand, calling `prove(IsPrime(v.x))` might yield an infinite sequence of proofs, one for each prime number the system can find.

"The right configuration" means having appropriate `Prover`s added to the knowledge base.

In fact, even checking if a formula is **directly** known (i.e. contained in the knowledge base's storage) is achieved with a built-in `Prover` which acts as a knowledge retriever (see section [Built-in Provers](#Built-in Provers)).

## Prover Objects

A `Prover` is built by passing:

- a "listened formula", which is what the `Prover` can prove (e.g. `IsPrime(?number)`)
- a "handler" function, which will be called when the prover is triggered
- an `argument_mode` enum value, which will determine how the triggering formula will be passed to the handler (see after the example right below)
- a `pass_substitution_as` value, which can be `None`, a string or the `Ellipsis` (`...`), and determines if and how the handler receives a substitution
- a `pure` boolean, which states whether the results produced by the prover are world-state-independent or not (see below [Verification](#Verification))
- a `safety` enum value, which states whether the prover performs only "safe" operations (i.e. things you don't mind happening a second time, like reading from a database vs writing on it) and controls how it is called in "safe" scenarios (hypothetical or verification)

An example usage of a `Prover` would work as follows:

```python
def is_prime(number: int):
    # here you perform your calculations and return a result
    ...

v = VariableSource()

prover = Prover(
    handler=is_prime, 
    listened_formula=IsPrime(v.number), 
    argument_mode=HandlerArgumentMode.MAP_UNWRAPPED,
    pass_substitution_as=...,
    pass_knowledge_base_as=...,
    pure=True, 
    safety=HandlerSafety.SAFE
)

kb.add_prover(prover)

kb.prove(IsPrime(wrap(13))
```

The `Prover` constructor argument `argument_mode=HandlerArgumentMode.UNWRAPPED_REQUIRED` tells the prover to unwrap a `LogicWrapper` before passing it to the function, and also to fail if an input variable is bound to anything but a `LogicWrapper` (intuitively, this is to write handlers that don't accept LogicObjects as inputs).

The possible values are:

- `RAW`: passes the matched `LogicObject` and the corresponding `Substitution` to the handler
- `MAP`: maps bound variables of the formula to the handler's arguments
- `MAP_UNWRAPPED`: like `MAP`, but automatically unwraps `LogicWrapper`s, any `LogicObject` is a valid input
- `MAP_UNWRAPPED_REQUIRED`: like `MAP`, but automatically unwraps `LogicWrapper`s, requires that all arguments receive a `LogicWrapper`
- `MAP_UNWRAPPED_NO_VARIABLES`: like `MAP`, but automatically unwraps `LogicWrapper`s and input variables can't be bound to logic `Variable`s
- `MAP_NO_VARIABLES`: like `MAP`, but input variables can't be bound to logic `Variable`s

With the `MAP*` options, `Variable` names in the trigger formula are matched to arguments in the handler, and it is required that **no homonymous variables are present** (although the same variable repeated is allowed) and that **all arguments in the handler must be present as variable names in the listened formula**, with the exception of the substitution (see right below the discussion of `pass_substitution_as`). Using a `VariableSource` is advised, to guarantee that a single name is associated to the same variable.

With the `RAW` option, the handler must take two argument: the first named "formula" and the second named according to` pass_substitution_as`. Homonymous variables are allowed.

As stated above, the `pass_substitution_as` argument determines if and how a substitution is passed to the handler, after being found by searching for proofs for a triggering formula (see [Proof Process](#Proof Process)). The possible values are:

- `...`/`Ellipsis` (the default): equivalent to `'substitution'` for `RAW` mode and to `None` for `MAP*` modes
- `None`: no substitution is passed to the handler, unsupported in `RAW` mode
- a string: the found substitution is passed to the handler as a keyword argument of the same name 

NOTE: there is no guaranteed relationship between the substitution passed to the handler and the `listened_formula`. To underline this the `listened_formula` is normalized by the `Prover`'s constructor, so `prover.listened_formula` is actually another formula, with "renewed" variables.

The `pass_knowledge_base_as` works similarly to `pass_substitution_as`, and allows to specify whether the handler will receive the current `KnowledgeBase` as input, and, if so, with what name. It accepts:

- `...`/`Ellipsis` (the default): equivalent to `None`
- `None`: no knowledge base is passed to the handler
- a string: the current knowledge base is passed to the handler as a keyword argument of the same name

Note that all values for `pass_knowledge_base_as` are allowed for all argument modes.

The `safety` argument is an enumerative value of type `HandlerSafety` can have the following values:

- `SAFE`: the prover will only perform operations that can be repeated without worry
- `TOTALLY_UNSAFE`: the prover performs "destructive" operations, and cannot be called in hypothetical scenarios or during verification
- `SAFE_FOR_HYPOTHESES`: the prover performs "destructive" operations, but can be used in hypothetical scenarios (see below [Hypothetical Scenarios](#Hypothetical Scenarios)) 

Besides performing arbitrary actions, a handler can return a variety of values, which intuitively mean that the handler has proven the input formula, possibly under some premises:

- nothing (`None`)
- a `Boolean`
- a `Substitution`
- a `Tuple[Boolean, Substitution]`
- a `Tuple[Boolean, Substitution, Proof]` where the `Proof` is the premise under which the result is returned, and it will be packed in another proof (see [Proof Process](#Proof Process))
    - instead of a single `Proof`, also an iterable of `Iterable[Proof]` is allowed
- a `TruthSubstitution` object
- a `TruthSubstitutionPremises` object
    
For all non-`None` and non-boolean values, an iterable of them is allowed (including tuples, since no ambiguity is possible).
    
## Proof Process

The `KnowledgeBase.prove(formula, *, retrieve_only, previous_substitution)` method starts a "proof" process, which proceeds as follows:

1. all provers that can prove the formula are retrieved
2. each prover's `prove(formula)` method is called, which in turn will call the handler, possibly passing the substitution (depending on `pass_substitution_as`)
3. each substitution returned by the handler with associated premises (if any) is then **possibly** packed in a `Proof` and yielded to the caller, unless a `False` boolean is returned, in which case the result is ignored (see section [Semantics](#Semantics) below for a discussion about why this is the case)

Each handler can recursively call the `prove` method. 

The process terminates if no more results are available from any provers, so it can be infinite, but is lazily-generated, so unless a single step takes forever this should be of little consequence.

The proof process returns zero or more `Proof`s, based on what the single provers returned. Each proof will have:

- as a conclusion, the formula that is being proven
- as a substitution, the substitution returned by the handler, or the one found before calling it if no substitution was returned
- as premises: all the premises returned by the handler
- as inference rule, the prover that produced the result

The `KnowledgeBase.prove(...)` method also accepts two further arguments:

- `retrieve_only`, if `True`, the only prover that will be used is the `KnowledgeRetriever` thus preventing any form of inference (see section [Built-in Provers](#Built-in Provers), the default is `False`
- `previous_substitution`, a `Substitution` which will be passed down the line to any `Prover.prove` call, the default is `None` 

## Open Formulas

Note that no constraint is placed on the listened_formula: it can be an open formula, and the proof process will gracefully skip any prover that does not support it, such as those with `MAP_NO_VARIABLES` mode.

The `RAW` mode directly receives the formula, while the `MAP*` modes can receive the variables directly as arguments.

An example where this could be useful is when trying to find "all the ways a formula is satisfiable", like finding all prime numbers.

In these cases, also passing the substitution to the handler is necessary, so that variables are kept.

## Built-in Provers

The currently built-in provers are the following:

- `RestrictedModusPonens`: a `RAW` mode prover which implements Modus Ponens (given `P`, it search for proofs of `Implies(?Q, P)` and, if successful, `?Q`), but won't take formulas like `Implies(?A, ?B)` as its input, to avoid infinite loops (this limitation might be removed in the future)
- `ClosedWorldAssumption`: a `RAW` mode prover which will only prove formulas like `Not(?P)`, and will return `True` if it cannot find a proof for `?P` (see [Semantics](#Semantics) and [Closed-world Assumption](#Closed-world Assumption) below)
    - NOTE: `ClosedWorldAssumption` is limited in that if a formula is `Not(?P)` it will **remove** the `Not`, but it won't add another one. This is to ensure termination.

Furthermore, every `KnowledgeBase` internally defines a "knowledge retriever", which accesses the internal storage.

## Semantics

Now what is this thing about ignoring results if they have a `False` boolean?

A `KnowledgeBase` is actually the implementation of an inference system. As such, you (sort of) can view it as an implicit specification of a set of logic formulas: instead of listing every formula belonging to the set, you specify some of them, and a way (inference rules) to deduce if other formulas belong to the set.

This is further expanded by the use of open formulas: when trying to prove an open formula P, all known ways of satisfying it (i.e. all formulas that can be proven to be part of the set and unify with P) are returned.

If the inference system cannot prove P, it might be able to prove ~P, or not. All depends on the system's properties (is it complete? does "tertium non datur" hold?). As such, the `KnowledgeBase` is designed to only answer to "does P belong to the set?", or, in other words, "can you prove P to be 'true'?".

One of the roles of `Prover`s is to provide "grounding" for their "predicates" (e.g. the `IsPrime` predicate in the example above), and in that case handlers will possibly be "absolute": defined externally without reference to proofs, knowledge bases or formulas. 

It is perfectly reasonable that such handlers return `True` or `False`: why would an external library implementing an `is_prime(x)` function only return `True` if x is prime, and not `False` if it's not? But again, the proof process can only prove formulas to be true, so **`False` values are ignored, because they literally serve no purpose to that end**.

### Handling False

How do you prove that a number is not prime? There is quite a simple solution:

1. create a new handler function `is_not_prime(x)` that returns `not is_prime(x)`
2. register a `Prover(listened_formula=Not(IsPrime(v.x)), handler=is_not_prime, ...)`

This will turn every `False` value to `True`, making the whole process work.

On the other hand, the handler could return something other than a boolean value, and this would require extra work and care, as it would probably be correct only for "absolute" handlers (those that don't know anything about proofs).

### Closed-world Assumption

There is another, more drastic option, to "handle false values", and that is the closed-world assumption: if you can't prove P is true, then P is false.

The closed-world assumption is implemented with the `ClosedWorldAssumption` prover, which tries to prove `Not(P)` by searching for proofs of `P` and returning `True` if no proofs could be found.

## Hypothetical Scenarios

A proof process is in a "hypothetical scenario" if at least one hypothesis is defined (with a hypothetical context).

A hypothetical scenario is considered unsafe, and as such if a prover is not safe it will not be used.

To run an unsafe prover, it is possible to mark it as `SAFE_FOR_HYPOTHESES`, but care should be taken to ensure that any operation is not based on hypotheses (or that it is ok to do so).

I can't think of a reasonable example right now for provers, so anyone interested should look at the corresponding section in the [listener documentation](listeners.md#Hypothetical Scenarios)

## Prover Indexing and Dynamic Provers

Provers are part of the machinery, not the data.

Provers are pure Python objects, that expose a "listened formula", which is used to index them in a separate in-memory storage. When a formula is being proven, it is matched with those in the provers storage to retrieve the correct provers.

This means that provers should be added "statically" when the knowledge base is being set up, and not dynamically by listeners (although this is not enforced, since some listeners could be part of the setup process if `ponder` is called on some "configuration formulas") (note: I am not considering the case where provers add other provers since I don't think it is reasonable).

This may be limiting, as we may want to allow the user to dinamically add new inference rules. An example of this could be Modus Ponens itself: the implication could be seen as the "inference rule", and `RestrictedModusPonens` searches for such a "rule" with the correct consequent, and then "dynamically chooses what antecedent to try and prove".

More generally, at least two approaches are possible:

- create a single prover that can prove any formula (i.e. its listened formula is a `Variable`)
  - the handler would be called in `RAW` mode and would:
    - search for `ProveWith(formula, ?handler)` on the knowledge base, where `?handler` will be bound to a user-defined handler
    - ask `?handler` to prove the formula
  - when the user adds a new dynamic prover for a formula and an action, it is actually added as a new `ProveWith(formula, handler)`
  - whenever a formula is being proven on, this prover will trigger and possibly do its thing
  - to ensure fairness to all "competing" provers, a round-robin or similar approach should be used to retrieve a single result from each prover in rotation
- create a single **listener** that listens for `ProveWith(?formula, ?handler)` (note that `?formula` is a variable now)
  - the handler would just create and dynamically add a `Prover` to the knowledge base
    - its handler would just perform whatever operations needed to return proofs
  - during application set-up, retrieve and ponder on all `ProveWith(?formula, ?handler)` formulas in the kb, so that provers are initialized
  - when the user adds a new dynamic prover for a formula and a handler, it is actually added as a new `ProveWith(formula, handler)` and then pondered to trigger the "master" listener
  - only pertinent formulas would then be passed to the "dynamic" provers

The first approach only adds one prover, which would improve startup time, while the second approach would probably be more efficient at runtime, since the prover storage is generally faster than the main knowledge storage.

## Conjunction and Disjunction

Proving conjunction is quite tricky, and no perfect solution is currently available.

For example, suppose we are trying to search for all prime numbers greater than 10. The query formula might be `And(IsPrime(?x), IsGreaterThan(?x, wrap(10)))`.

A naive approach could be: search for proofs for the first conjunct, then for each search for proofs for the second one. This would list all prime numbers, and for each check if it's greater than 10, which is very inefficient if, instead of 10, we passed a very large number.

Proceeding in reverse order wouldn't help in the general case.

Another approach could be:

- create two provers:
    - the first:
        - takes any formula
        - checks that it is a conjunction
        - sorts the conjuncts (I'm not sure this is always possible, but it should be possible under reasonable assumptions, such as the predicate of each conjunct being a single `Constant`, so this prover would be quite general)
        - tries to prove the sorted version (possibly changing `And` with some special `Conjunction` symbol, to avoid unnecessary recursion)
    - the second
        - takes `Conjunction(A, B)`, where A and B unify respectively with the first and second conjunct of the original formula, according to the defined ordering
        - performs a custom, optimized algorithm, to handle both
         
I haven't analyzed disjunction (so, yes, the title of this section is a terrible lie :P), but I assume it will present similar challenges.

The main takeaway here is: unless unification is changed to allow order-independence, sorting conjuncts (and possibly disjuncts) is your best friend.

 ## Verification
 
 A proof produced by a proof process has the `Prover` that generated it as its prover.
 
 Depending on the purity and the safety of the prover, the proof will be verified in different ways:
 
 - if the prover is pure, its premises are recursively verified, and that is all
 - if the prover is not pure
    - if it is `SAFE`, its premises are recursively verified, then used as knowledge context (i.e. added either to hypotheses or to a temporary knowledge base containing only those proofs) to call the prover's `prove(...)` method, passing the conclusion
    - if it is not `SAFE`, the proof is not verifiable, and as such will be discarded
 
 `SAFE`, impure provers will be triggered at every verification. This could in turn request one or more proofs, possibly huge ones.
 
 However, this is not as inefficient as it sounds: since the premises are verified beforehand, a well-designed prover will already find all the information it needs, while a badly designed one will probably find no proofs and fail verification. The only repeated operations would (or at least should) be those that caused the prover to be marked as impure, like reading a database or a file.
 