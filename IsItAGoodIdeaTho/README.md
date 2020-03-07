# Oh no, what am I doing?

I recently learned Go for a work project, and I mostly dislike the language, although I **LOVE** goroutines (who doesn't?) and channels.

Also, I recently stumbled upon [new features in Julia 1.3 for tasks and threads](https://docs.julialang.org/en/v1/NEWS/#Multi-threading-changes-1).

My issues with Go are the total lack of elegance (it seems a patchwork of features to me) and the terrible type system.

Julia suffers (in my opinion) from the same "also throw that in the bucket", but has a few advantages over Go:

1. the language is more elegant: even though it has a shit-load more things, it feels like it is more "efficient" in providing semantic features with syntactic ones, so it feels smaller
2. it has a better type-system, even though it is a dynamic one
3. it has built-in distributed computing features
4. MACROS

I'm not going to actually argue any of these, mainly because I just read the manual of both languages (and used Go at work), so... yeah

## Wait, why am I talking about Go?

Ok, I just wanted to rant a little about Go :)

The main point is this: Julia has **many** issues, but I think it is (and increasingly will be) a great general-purpose language.

It's very young, and seems quite immature, but it is very promising, to the extent that it might end up being my favourite language.

So... I'm considering switching to Julia for this project (actually, I'm considering Julia for all of my projects).

## Oh no, what am I doing? (cont.)

I'm not sure yet, the project is still young (I still haven't even revealed its real name! :D), should I switch language now?

- (hypothetical) pros:
  - julia is faster
  - julia is amazing at parallelism
  - julia has MACROS!
  - the project is still small, so not a lot of code needs rewriting
  - I was considering a total rewrite, just because I like rewriting things :D
- cons:
  - julia is immature (project structure, libraries...)
  - libraries are ugly (I don't like the import system)
  - I don't know it as well as Python (I've been studying it for a week in my spare time)
  - this might be a form of early optimization in disguise

The outcome of this totally sound formulation is clear: I'll give Julia a shot.

## The evil plan

I had a plan involving fleas and lots of boxes, but in order to save on postage I switched to the following instead:

- [ ] benchmarks + feasibility
  - [ ] benchmark unification in both languages
  - [ ] implement id auto-generation (because of what is said [here](https://docs.julialang.org/en/v1/manual/modules/#Module-initialization-and-precompilation-1), which worries me since I'm too lazy/stoopid to actually understand the implications just by reading)
  - [ ] implement parallelism in Julia
    - [ ] single-threaded (what I would have done in Python with greenlet)
    - [ ] multi-threaded (I mean, since we are already here)
  - [ ] implement a context mechanism (so that provers can use it to call the current knowledge base)
  - [ ] benchmark the AbstruseIndex in both languages
  - [ ] draw some conclusions while nodding wisely
- [ ] either do the translation or declare that python stays
- [ ] remember that I created this branch from the wrong one, even though I don't think it'll have any consequences
- [ ] ???
- [ ] profit

Ready? Go! I mean... Julia! :D (sorry)