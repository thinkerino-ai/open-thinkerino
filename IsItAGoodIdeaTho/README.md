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

- [nope] benchmarks + feasibility
  - [x] benchmark unification in both languages
  - [x] implement id auto-generation (because of what is said [here](https://docs.julialang.org/en/v1/manual/modules/#Module-initialization-and-precompilation-1), which worries me since I'm too lazy/stoopid to actually understand the implications just by reading)
  - [x] implement parallelism in Julia
    - [x] single-threaded (what I would have done in Python with greenlet)
    - [x] multi-threaded (I mean, since we are already here)
  - [x] implement a context mechanism (so that provers can use it to call the current knowledge base)
  - [nope] benchmark the AbstruseIndex in both languages
  - [nope] draw some conclusions while nodding wisely
- [nope] either do the translation or declare that python stays
- [nope] remember that I created this branch from the wrong one, even though I don't think it'll have any consequences
  - [nope] but there are fixes to the python part now :/ sigh, I'll have to merge or something like that
- [nope] ???
- [nope] profit

Ready? Go! I mean... Julia! :D (sorry)

## Some notes

- the tools are currently very immature, I'm using vs-code since Juno marks errors on things that it shouldn't
  - a debugger is absent, but I'm managing with Debugger.jl, and [there is something on its way](https://github.com/julia-vscode/julia-vscode/issues/125)
  - static type-checking is absent, I've heard people say that "Julia is a dynamic language", and that is true, but even if one can't infer "all truths" about types at parse-time, it's still worth it to find those cases where an error IS detectable (just see python with mypy)
  - intellisense is somewhat unreliable, and the linter will sometimes tell you "this does not exist" when it does
- lack of coroutines is TERRIBLE! I need them! I abuse them! however, channels are really cool, and I might like the structure of my `parallelism.jl` experiment better than the @prover_function I was using in python (explicit proof_channel is nice, although it reduces the magic... huh)
  - I really enjoyed the `@async ... @sync ... @async` shenanigans I could do in the single-threaded version

-----

## The moral of the story

So... it's been a few weeks since I've started this, and in the last two weeks I've been fighting myself about this, but I guess this is it: I'm giving up on Julia, at least for now.

There were a few key points that made me **LOVE** Julia and prefer it over Python:

1. fast performance
2. a nice type system
3. macros
4. actual multithreading (fuck you, GIL)
5. built-in distributed computing
6. Go-style coroutines, but better (explicit `yield()` allow so much more control)
7. channels

That said, while trying to implement my AbstruseIndex, I had a few issues:

1. performance is great if you know what you're doing, but most of the time I don't
2. no generator functions (yet)
3. numbers are iterable (this. is. terrible.)
4. NoSQL (and more) support is nearly non-existent (yet)
5. tools
6. no custom scheduling (yet)

I'll explain each one

### 1. Performance

In a simple benchmark for unification I found Julia to be 100x faster than Python. I jumped on my chair in disbelief, that was incredible! And to think that it was just single-threaded code, the world was my oyster.

A more complex benchmark (with larger formulas) put numbers in perspective: Julia was "only" 8x-10x faster than Python. Less exciting, but still, a 10x performance increase **for free** was incredible, even more so considering Julia allows actual multi-threading (and my code is mostly pure, so it benefits a lot from multi-threading).

But then I tried implementing the `AbstruseIndex`, and in particular the `make_key` function, and Julia was actually 10x **slower** than Python.

Wut.

After some investigation it turned out that the `applicable(iterate, x)` function that I was using to find out if the current element was iterable is very slow. I changed it into a `isa(Array, x)` and boom, Julia was 10x faster again, the music resumed and the sun was shining once more.

Then I moved onto the actual `AbstruseIndex`, and since its `retrieve` method is actually just a tree-visiting algorithm, I began with writing a simple "nested-list flattener".

The benchmark were not in Julia's favor, as this

```julia
function tree_iterator(chn::Channel{Int}, tree::Union{Array,Int})
    if isa(tree, Array)
        for sub::Union{Array,Int} in tree::Array
            tree_iterator(chn, sub)
        end
    else
        push!(chn, tree::Int)
    end
end

using BenchmarkTools
@benchmark collect(Channel{Int}() do c tree_iterator(c, [[1,2,3], [4,5,6]]) end)
```

was slower than this

```python
def tree_iterator(tree): 
    if isinstance(tree, list): 
        for sub in tree: 
            yield from tree_iterator(sub) 
    else: 
         yield tree 

from timeit import timeit
timeit(lambda: list(tree_iterator([[1,2,3], [4,5,6]])))
```

Did I do something wrong? I don't know, possibly. I'm sure I still need (and want!) to learn how to write Julian code, but:

- I like the Python syntax much more (in this case)
- it is not obvious to me how to make this faster

This was not a deal-breaker: after the initial heartbreak I realized that my love for Julia would continue, as it had so much more to offer.

### 2. Generators

This is quite simple: Julia doesn't have a `yield` statement, so it's impossible to write generator functions.

I really like channels, even though they force you to take an additional argument in functions, as they are much more powerful, but sometimes I'd like to just write my function with my `yield`s and `yield from`s, just for fun, you know.

And yes, I know about ResumableFunctions.jl and that-other-one-of-which-I-don-t-remember-the-name.jl, but they are a workaround. I want true generators because then I can iterate, collect, get a single element and so on.

Once more, this was not a deal-breaker, but still... I want a language that gives me more, not less.

### 3. Iterable Numbers

I mean... WHAT?

This may be the ugliest thing in Julia.

I can accept 1-based arrays, it's quirky, but it's arbitrary, and also Julia has `firstindex` and `lastindex` which create an abstraction that, to me, is much cooler than being 0-based.

I can, in fact, accept many things.

But a number is NOT iterable. There is not a "first element in a number" because **THAT IS NOT A FUCKING THING**. 

In set theory a number is **not** a set, so while it makes sense to say `1 ∈ Set([1,2,3])` (valid Julia expression) or even `1 ∈ [1,2,3]`, you cannot write `1 ∈ 1`, because `1` is not a set! It is not an iterable! It is a number.

That said, it took me a few days to let the steam off and think about all the nice things about Julia.

Once again, this was not a deal-breaker.

### 4. NoSQL support

I began considering switching to Julia while I was working on persistence in Python (more precisely, I was taking a break because I'm lazy, but that was the "current task").

In Python I was using Redis, so the first thing I checked in Julia was "is there a Redis client?" and the answer is, luckily, [yes](https://github.com/JuliaDatabases/Redis.jl).

I was satisfied, because my only dependencies in Python are (currently) only Redis and Greenlet, and since Julia has Go-style coroutines I don't need some Greenlet alternative.

But then it hit me: I don't want to use redis, I want to use a graph database! Or maybe not? Maybe something else?

The point is, I started seeing all the limitations of using a language with a less-than-mature ecosystem.

But there was a solution: use PyCall.jl, so that Python clients become available in Julia.

And that was it, another issue that I could accept, not a deal-breaker.

### 5. Tools

Yeah... as I write I'm using vscode (I don't like Juno and I had a few issues with it), with julia-vscode extension (v 0.13).

It's nice, and I really like vscode, but:

- no debugger
- the linter is "buggy"

Also, the linter cannot perform static type-checking (like mypy in Python), which is VERY important for me, as I'm a fan of static checks.

The point is: tools are not mature enough (or even available) yet.

But again, I can use the command-line debugger, and a friend of mine once told me: static typing is a waste of time, if you are self-disciplined and careful enough, you don't ever make type mistakes.

I'm not self-disciplined or careful **AT ALL**, but I can live with that: I'd simply write more tests and pretend those are my checks.

So, again, not a deal-breaker.

### 6. Custom scheduling

After persistence the next big task for this project would have been concurrency.

My idea was: proofs should be able to proceed concurrently, even if on a single thread, so that I can both prove multiple things at the same time and make sub-proofs concurrent. Then I would write some sort of mechanism to sync multiple processes, both on the local machine (fuck you GIL) and remote, to make a nice distributed system.

Then Julia came, which had multiple threads, the `yield()` function, and even remote channels.

It was like all I was planning to do was done by somebody else, gift-wrapped with a "better-performance" bow.

But then... I began experimenting, and I realized that there is no control over the scheduling of tasks.

This means that I can't run proofs with different priorities and stuff like that.

And that, considering the roadmap I have in mind for this project, is a deal-breaker ._.