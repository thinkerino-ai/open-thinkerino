module index 
using ..logic.core
using Base.Iterators
export make_key

_make_key(obj::core.Expression, depth::Int) = begin 
    if depth == 0
        return length(obj.children)
    else
        return (
            map(
                # ugly, but it is all a consequence of how numbers are iterable, please don't ask
                (c -> make_key(c, depth - 1)  |> (x -> isnothing(x) ? () : isa(x, AbstractArray) ? x : (x,))), 
                obj.children
            ) 
            |> flatten 
        )
    end
end

make_key(obj::core.LogicObject, depth::Int) = depth == 0 ? obj : nothing
make_key(obj::core.Variable, depth::Int) = depth == 0 ? core.Variable : nothing
make_key(obj::core.Expression, depth::Int) = begin 
    # TODO: optimize this garbage :P
    # you have no how much attempts I had to make before this was faster than the pyhton version <.<
    if depth == 0
        return length(obj.children)
    else
        res = Array{Any, 1}()
        for child in obj.children
            key = make_key(child, depth - 1)
            if isa(key, AbstractArray)
                for k in key
                    push!(res, k)
                end
            elseif !isnothing(key)
                push!(res, key)
            end
        end
        return res
    end
end
#(a, (b, x), (y, y), z)
end ##module