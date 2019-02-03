# Logic

This package handles "logic expressions", structures strongly inspired by logic formulas.

## Quickstart

```python
from aitools.logic.utils import variables, logicObjects, expr
from aitools.logic import Substitution

# you can create a variable with v = Variable(), or use the utility 'variables()' that returns a generator
v1, v2 = variables(2)
# 
a, b, c, d = logicObjects(4) # more verbose syntax
e1 = (a, (b, c), [d]) >> expr # alternative syntax: (a, (b, c), (d,)) >> expr
e2 = (a, (v1, c), v2) >> expr
Substitution.unify(e1,e2)
# Result: Substitution({Variable(0): Binding(frozenset({Variable(0)}), head=o3), Variable(1): Binding(frozenset({Variable(1)}), head=(o5))})
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