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

"""
    project_key(projector_key, optics_key, current_key)

Expands the `current_key` by "projecting" variables in the `projector_key` through the "lenses" in the `optics_key`.
"""
function project_key(projector_key, optics_key, current_key)
    key = @view current_key[:]
    result = []

    for (i, lens) in enumerate(optics_key)
        if projector_key[i] === core.Variable && isa(lens, Int)
            append!(result, repeated(core.Variable, lens))
        elseif isa(lens, Int)
            append!(result, @view key[1:lens])
            key = @view key[lens + 1:end]
        end
    end

    append!(result, key)

    return result
end

end ##module