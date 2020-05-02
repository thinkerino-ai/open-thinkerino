# Listeners

The `KnowledgeBase.ponder(...)` method provides a way for the system to react to formulas.

For example, if an email is received, you could call `ponder(EmailReceived(some_email))`, where `some_email` could be a `LogicWrapper` to the email object. This could in turn trigger some operation, like checking if the sender is a co-worker and search a vacation calendar and, if necessary, provide a polite automatic response.

This custom behaviour is enabled by a `Listener`. `Listener`s are modules that can be added to the knowledge base to expand its behaviour.

## Listener Objects

A `Listener` is built by passing:

- a "listened formula", which is what the `Listener` listens for (e.g. `EmailReceived(?email)`)
- a "handler" function, which will be called when the listener triggers
- an `argument_mode` enum value, which will determine how the triggering formula will be passed to the handler (see after the example right below)
- a `pure` boolean, which states whether the results produced by the listener are world-state-independent or not (see below [Verification](#Verification))
- a `safety` enum value, which states whether the listener performs only "safe" operations (i.e. things you don't mind happening a second time, like reading from a database vs writing on it) and controls how it is called in "safe" scenarios (hypothetical or verification)

An example usage of a `Listener` would work as follows:

```python
def handle_email(email: Email):
    # do here what you want with the Email
    ...

v = VariableSource()

listener = Listener(
    handler=handle_email, 
    listened_formula=EmailReceived(v.email), 
    argument_mode=HandlerArgumentMode.MAP_UNWRAPPED, 
    pure=True, 
    safety=HandlerSafety.TotallyUnsafe
)

kb.add_listener(listener)

# I have no idea how to make this look realistic :P
some_email = Email(sender="your friend", object="cat picture", body=...)

kb.ponder(EmailReceived(wrap(some_email), closed=True)
```

The `Listener` constructor argument `argument_mode=HandlerArgumentMode.UNWRAPPED_REQUIRED` tells the listener to unwrap a `LogicWrapper` before passing it to the function, and also to fail if an input variable is bound to anything but a `LogicWrapper` (intuitively, this is to write handlers that don't accept LogicObjects as inputs).

The possible values are:

- `RAW`: passes the matched `LogicObject` and the corresponding `Substitution` to the handler
- `MAP`: maps bound variables of the formula to the handler's arguments
- `MAP_UNWRAPPED`: like `MAP`, but automatically unwraps `LogicWrapper`s, any `LogicObject` is a valid input
- `MAP_UNWRAPPED_REQUIRED`: like `MAP`, but automatically unwraps `LogicWrapper`s, requires that all arguments receive a `LogicWrapper`
- `MAP_UNWRAPPED_NO_VARIABLES`: like `MAP`, but automatically unwraps `LogicWrapper`s and input variables can't be bound to logic `Variable`s
- `MAP_NO_VARIABLES`: like `MAP`, but input variables can't be bound to logic `Variable`s

With the `MAP*` options, `Variable` names in the trigger formula are matched to arguments in the handler, so creating them from a single `VariableSource` is advised (to guarantee that a single name is associated to the same variable).

The `safety` argument is an enumerative value of type `HandlerSafety` can have the following values:

- `Safe`: the listener will only perform operations that can be repeated without worry
- `TotallyUnsafe`: the listener performs "destructive" operations, and cannot be called in hypothetical scenarios or during verification
- `SafeForHypotheses`: the listener performs "destructive" operations, but can be used in hypothetical scenarios (see below [Hypothetical Scenarios](#Hypothetical Scenarios)) 

A handler can return:

- nothing (`None`)
- a `LogicObject`
    - an iterable of them is allowed (e.g. generator functions)
- a pair <`LogicObject`, premises> where the "premises" are an iterable of `Proof`s that the listener used to base its output on
    - an iterable of them is allowed
    
## Pondering Process

The `KnowledgeBase.ponder(formulas, ponder_mode)` method starts a "pondering" process, which proceeds as follows for each of the formulas:

1. the formula is checked to be satisfiable, either by `retrieve` or `prove`, depending on the `ponder_mode`
2. for each of the satisfying formulas, all listeners that it can trigger are retrieved
3. each listener's `ponder(formula)` method is called, which in turn will call the handler
4. each returned formula by the listener, with its premises (if any) is then packed in a `Proof` and yielded to the caller
5. each returned formula by the listener is also further used for step 2

The process terminates if no more formulas are available, so it can be infinite, but is lazily-generated, so unless a single step takes forever this should be of little consequence.

The `ponder_mode` is an enumerative value of type `PonderMode` with the following options:

- `PonderMode.Known`: all formulas must be already known, `KnowledgeBase.retrieve(...)` is used (no proofs are searched)
- `PonderMode.Prove`: all formulas must be provable, `KnowledgeBase.prove(...)` is used
- `PonderMode.Hypothetically`: all formulas are added as hypotheses before proceeding, no check is required (we are adding them, we should know we did!)

The pondering process returns zero or more `Proof`s, based on what the single listeners returned. Each proof will have:

- as a conclusion, the formula returned by the listener's handler
- as premises
    - all the premises returned by the listener's handler
    - the triggering formula (I'm not sure about this, but for now it is like that)
- as inference rule, a `Pondering`, which wraps the listener and the triggering formula

## Hypothetical Scenarios

A pondering process is considered to happen in a "hypothetical scenario" if at least one hypothesis is defined, either from the outside (with a hypothetical context), or by the process itself, when `PonderMode.Hypothetically` is used.

A hypothetical scenario is considered unsafe, and as such if a listener is not safe it will not be triggered.

To run an unsafe listener, it is possible to mark it as `SafeForHypotheses`, but care should be taken to ensure that any operation is not based on hypotheses (or that it is ok to do so).

For example, suppose that we have the hypothesis `IsCoworker(john)`, and that we ponder on an email received by John. The handler could have the following code:

```python
# TODO the API is terrible, I need to do something about it :P
def handle_email(email: Email):
    sender = email.sender
    # we only respond to coworkers
    for proof in prove(IsCoworker(wrap(sender))):
        # but only to those that are based on actual knowledge
        if not proof.is_hypothetical:
            # if you write "fuckerino" it is not a swear-word, so it is not rude
            email.respond(f"Dear {sender.name},\nI'm on vacation, please shut the fuckerino up")
```

As the example shows, it is quite complex to manually ensure safety, so `HandlerSafety.TotallyUnsafe` should be used in most cases when destructive operations are performed.

## Listener Indexing and Dynamic Listeners

Listeners are part of the machinery, not the data.

Listeners are pure Python objects, that expose a "listened formula", which is used to index them in a separate in-memory storage. When a formula is pondered on, it is matched with those in the listener storage to retrieve the correct listeners.

This means that listeners should be added "statically" when the knowledge base is being set up, and not dynamically by other listeners (although this is not enforced, since some listeners could be part of the setup process if `ponder` is called on some "configuration formulas").

This may be limiting, as we may want to allow the user to dinamically provide "triggers" of some sort. For example, an application could expose a scripting language to describe procedures, and allow the user to say "if this, then that" (no copyright infringement intended, but "pun" totally intended :P).

This can be easily solved in at least two ways:

- create a single listener that listens for any formula (i.e. its listened formula is a `Variable`)
  - the handler would be called in `RAW` mode and would:
    - search for `ListenFor(formula, ?action)` on the knowledge base, where `?action` will be bound to the user-defined procedures
    - run the resulting bindings for `?action` with some "execute" functionality
  - when the user adds a new dynamic listener for a formula and an action, it is actually added as a new `ListenFor(formula, action)`
  - whenever a formula is pondered on, this listener will trigger and possibly do its thing
- create a single listener that listens for `ListenFor(?formula, ?action)` (note that now `?formula` is a variable now)
  - the handler would just create and dynamically add a `Listener` to the knowledge base (yes, the very thing I said you shouldn't normally do :P)
    - its handler would just execute the action
  - during application set-up, retrieve and ponder on all `ListenFor(?formula, ?action)` formulas in the kb, so that listeners are initialized
  - when the user adds a new dynamic listener for a formula and an action, it is actually added as a new `ListenFor(formula, action)` and then pondered to trigger the "master" listener
  - only pertinent formulas would then trigger the correct "dynamic" listener

The first approach only adds one listener, which would improve startup time, while the second approach would probably be more efficient at runtime, since the listener storage is generally faster than the main knowledge storage.

## Multi-listeners (a.k.a. the planets align)

As stated above, listeners only take a single listened formula, and are called with a single triggering formula. This is by design, to allow for simple and efficient implementation of most listeners.

However, if one wanted to listen for multiple conditions to be true, the following approach could solve it:

- subclass `Listener`, so that the constructor can take all the conditions in a "secondary parameter"
- create one listener for each condition, with the `HandlerArgumentMode.RAW` option, and passing all the conditions as the secondary parameter
- the handlers should all have a reference to the whole set of conditions, and check for the other conditions (through `prove` or `retrieve`) to be satisfiable
- all calls to the handlers will not actually do anything, except for the last one, which will find all other conditions to be true, and cand then call the "real handler"

This approach only works when formulas are added to the knowledge base as well, or if all formulas are passed at the same time (or produced during the same pondering).

A "cache" storage could also be implemented to keep track of increasingly satisfied condition sets, and passed to all listeners. In this case, care should be taken to prevent excessive memory usage.
 
 ## Verification
 
 A proof produced by a pondering process has a `Pondering` object as its prover. The object has a reference to the listener that produced it and to the triggering formula.
 
 Depending on the purity and the safety of the listener, the proof will be verified in different ways:
 
 - if the listener is pure, its premises are recursively verified, and that is all
 - if the listener is not pure
    - if it is `Safe`, its premises are recursively verified, then used as knowledge context (i.e. added either to hypotheses or to a temporary knowledge base containing only those proofs) to call the listener's `ponder(...)` method, passing the triggering formula
    - if it is not `Safe`, the proof is not verifiable, and as such will be discarded
 
 `Safe`, impure listeners will be triggered at every verification. This could in turn request one or more proofs, possibly huge ones.
 
 However, this is not as inefficient as it sounds: since the premises are verified beforehand, a well-designed listener will already find all the information it needs, while a badly designed one will probably find no proofs and fail verification. The only repeated operations would (or at least should) be those that caused the listener to be marked as impure, like reading a database or a file.
 