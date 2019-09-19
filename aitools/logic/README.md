# Logic

This package handles "logic expressions", structures strongly inspired by logic formulas.

## Quickstart

```python
from aitools.logic.utils import variables, logicObjects, expr
from aitools.logic import Substitution

# you can create a variable with v = Variable(), or use the utility 'variables()' that returns a generator
v1, v2 = variables('v1, v2')
# create "constants", equivalent to calling Constant() 3 times
b, c, d = constants('b, c, d')
e1 = expr("hello", ("yay", c), [d]) # alternative syntax: expr("hello", (b, c), (d,))
e2 = expr("hello", (v1, c), v2)
# unification
unifier = Substitution.unify(e1,e2)
```

## Theor-ish

Logic formulas (see for example [First Order Logic](https://en.wikipedia.org/wiki/First-order_logic)) are structures composed of various kinds of entities called "symbols".

For example, the formulas `(∀?x)(Human(?x)=>Mortal(?x))` and `Human(socrates)` contain a variety of symbols, like:

- the universal quantifier `∀` (for all)
- a variable `?x`, which acts
- a constant `socrates`
- the predicate symbols `Human` and `Mortal`

Two key concepts are those of **substitution** and **unification**. Intuitively, the former assigns a value to a variable, while the latter is the process of finding the substitutions that can make two formulas identical.

For example, the unification of formulas `Human(?x)` and `Human(socrates)` results in a single substitution `?x -> socrates`, which means "replace occurrences of `?x` with the constant `socrates`". In logic formulas there are a few restrictions and much more formality.

While I **LOVE** formal definitions, I also like freedom, so... yeah. Keep on reading.

## Details

IOU a great explanation :)
