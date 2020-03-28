using IsItAGoodIdeaTho.logic.core
using IsItAGoodIdeaTho.logic.unification: unify
using IsItAGoodIdeaTho.index: make_key
using BenchmarkTools: @benchmark
using IsItAGoodIdeaTho.index: make_key, project_key


a, b, c, d = Constant(), Constant(), Constant(), Constant()
x, y, z, w, s = Variable(), Variable(), Variable(), Variable(), Variable()

# e1 = Expression([a, x])
# e2 = Expression([y, b])

# (a, (b, x), (y, y), z)
e3 = Expression([a, Expression([b, x]), Expression([y, y]), z])
# (a, (x, b), ((c, s), (w, d)), (s, w))
e4 = Expression([a, Expression([x, b]), Expression([Expression([c,s]), Expression([w,d])]), Expression([s,w])])

#@benchmark unify(e3, e4)

#= python version
def foo():
    a, b, c, d = Constant(), Constant(), Constant(), Constant()
    x, y, z, w, s = Variable(), Variable(), Variable(), Variable(), Variable()
    e3 = Expression(a, Expression(b, x), Expression(y, y), z)
    e4 = Expression(a, Expression(x, b), Expression(Expression(c,s), Expression(w,d)), Expression(s,w))
    return Substitution.unify(e3, e4)
=#
    
#@benchmark make_key(e4, 3)

key2 = [a, Variable, 2, b]
key3 = [d, d]

optics_key = [a, 2, 2, b]

@benchmark project_key(key2, optics_key, key3)