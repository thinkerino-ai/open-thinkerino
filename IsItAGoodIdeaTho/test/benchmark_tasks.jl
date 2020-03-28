using Pkg
#Pkg.add("BenchmarkTools")
using BenchmarkTools

function single()
    xs = []
    function foo()
        for i in 1:10000
            push!(xs, i)
        end
    end
    foo()
end

function double()
    xs::Array{Int} = []
    function foo()
        for i in 1:5000
            push!(xs, i); yield()
        end
    end
    function bar()
        for i in 5001:10000
            push!(xs, i); yield()
        end
    end
    @sync begin
        @async foo()
        @async bar()
    end
    return xs
end

function tree_iterator(chn::Channel{Int}, tree::Union{Array,Int})
    if isa(tree, Array)
        for sub::Union{Array,Int} in tree::Array
            tree_iterator(chn, sub)
        end
    else
        push!(chn, tree::Int)
    end
end

function tree_iterator_async2(chn::Channel{Int}, tree::Union{Array,Int})
    if isa(tree, Array)
        @sync for sub::Union{Array,Int} in tree::Array
            @async tree_iterator_async(chn, sub)
            yield()
        end
    else
        push!(chn, tree::Int)
    end
end

function tree_iterator_async(chn::Channel{Int}, tree::Array)
    @sync for sub in tree
        if isa(sub, Int)
            push!(chn, sub)
            yield() # but why? why do I need this?
        else
            @async tree_iterator_async(chn, sub)
        end
    end
end

println(collect(Channel{Int}(0) do c 
    tree_iterator_async(c, [[1,2,3,4], [5,6,7,8], [9,10,11,12]]) 
end))

# chn = Channel{Int}() do c 
#     tree_iterator_async(c, [[1,2,3],[4,5,6],[7,8,9]])
# end
# println(take!(chn))
# println(take!(chn))
# println(take!(chn))

# println(@benchmark single())

# println(@benchmark double())

# def double(): 
#     xs = [] 
#     def foo(): 
#         for i in range(5000): 
#             xs.append(i) 
#             yield None 
#     def bar(): 
#         for i in range(5000, 10000): 
#             xs.append(i) 
#             yield None 
#     iterfoo = foo() 
#     iterbar = bar() 
#     while True: 
#         try: 
#             next(iterfoo) 
#             next(iterbar) 
#         except StopIteration: 
#             break 
#     return xs 


# def tree_iterator(tree): 
#     if isinstance(tree, list): 
#         for sub in tree: 
#             yield from tree_iterator(sub) 
#     else: 
#          yield tree 