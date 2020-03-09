module unification
using ..core

struct UnificationError <: Exception 
    message
end

struct Binding{THead <: Union{core.LogicObject,Nothing}} <: core.LogicObject
    head::THead
    variables::Set{core.Variable}

    function Binding(::Nothing, variables::Set{core.Variable})
        var_count = length(variables)
        if var_count < 2
            throw(ArgumentError("If no head is specified there must be at least two variables"))
        end
        # TODO I've been writing Julia for 5 minutes and I already have duplicated code :/
        if var_count < 1
            throw(ArgumentError("There must be at least one variable"))
        end
        return new{Nothing}(nothing, variables)
    end
    
    function Binding(head::core.LogicObject, variables::Set{core.Variable})
        var_count = length(variables)
        # TODO I've been writing Julia for 5 minutes and I already have duplicated code :/
        if var_count < 1
            throw(ArgumentError("There must be at least one variable"))
        end
        if any(core.appears_in(v, head) for v in variables)
            throw(ArgumentError("The head of a binding cannot contain its variables"))
        end
        return new{core.LogicObject}(head, variables)
    end
end

struct Substitution <: core.LogicObject
    # TODO make this a Base.ImmutableDict
    bindings_by_variable::Dict{core.Variable,Binding}
end

Substitution() = Substitution(Dict{core.Variable,Binding}())

# TODO just like in python, the "max" is super inefficient :P
get_head(binding::Binding{Nothing}) = max(v->v.id, binding.variables)
get_head(binding::Binding{core.LogicObject}) = binding.head

Base.union(a::Binding, b::Binding, binding_context::Nothing=nothing) = union(a, b, Substitution())
Base.union(a::Binding{core.LogicObject}, b::Binding{core.LogicObject}, binding_context::Substitution) = let unifier = unify(a.head, b.head, previous=binding_context)
    if isnothing(unifier)
        throw(UnificationError("Unable to unify the heads of the two bindings"))
    end
    return Binding(apply_substitution(unifier, a.head), a.variables ∪ b.variables)
end

Base.union(a::Binding, b::Binding, binding_context::Substitution) = Binding(nothing, a.variables ∪ b.variables)
    
Base.isempty(subst::Substitution) = Base.isempty(subst.bindings_by_variable)

function Substitution(bindings::Binding...)
    bindings_dict = Dict{core.Variable,Binding}()
    # TODO refactor to common function (with_bindings), just like it was in python
    for binding in bindings
        # TODO in python I make a copy of binding, does this work?
        merged_binding = binding
        for v in binding.variables
            other = get(bindings_dict, v, nothing)
            if ~isnothing(other)
                merged_binding = merged_binding ∪ other
            end
        end
        for v in merged_binding.variables
            bindings_dict[v] = merged_binding
        end
    end
    return Substitution(bindings_dict)
end

function with_bindings(subst::Substitution, bindings::Binding...)
    bindings_dict = copy(subst.bindings_by_variable)
    # TODO refactor to common function (Substitution constructor), just like it was in python
    for binding in bindings
        # TODO in python I make a copy of binding, does this work?
        merged_binding = binding
        for v in binding.variables
            other = get(bindings_dict, v, nothing)
            if ~isnothing(other)
                merged_binding = merged_binding ∪ other
            end
        end
        for v in merged_binding.variables
            bindings_dict[v] = merged_binding
        end
    end
    return Substitution(bindings_dict)
end

apply_substitution(::Substitution, obj::core.LogicObject) = obj

apply_substitution(subst::Substitution, obj::core.Expression) = core.Expression(map(c -> apply_substitution(subst, c), obj.children))

apply_substitution(subst::Substitution, obj::core.Variable) = begin
    if obj in keys(subst.bindings_by_variable)
        binding = subst.bindings_by_variable[obj]
        # TODO this is a little different than in python because I'm re-using 'get_head', while in python I apparently forgot to (but I also used the wrong name 'get_bound_object_for' for the get_head, so... yeah)
        return get_head(binding)
    else
        return obj
    end
end

function get_bound_object_for(subst::Substitution, variable::core.Variable)::Union{core.LogicObject,Nothing}
    return variable in keys(subst.bindings_by_variable) ? get_head(subst.bindings_by_variable[variable]) : nothing
end

unify(a, b, previous::Nothing=nothing) = unify(a, b, Substitution())
unify(a, b, previous::Substitution) = begin
    a = apply_substitution(previous, a)
    b = apply_substitution(previous, b)
    if a == b
        return previous
    else
        return _unify(a, b, previous)
    end
end

_unify(a::core.Variable, b::core.Variable, previous::Substitution) = with_bindings(previous, Binding(nothing, Set((a, b))))
_unify(a::core.Variable, b, previous::Substitution) = core.appears_in(a, b) ? nothing : with_bindings(previous, Binding(b, Set((a,))))
_unify(a, b::core.Variable, previous::Substitution) = core.appears_in(b, a) ? nothing : with_bindings(previous, Binding(a, Set((b,))))
_unify(a::core.Expression, b::core.Expression, previous::Substitution) = begin
    child_unifier = nothing
    if length(a.children) != length(b.children)
        return nothing
    end

    for (a_child, b_child) in zip(a.children, b.children)
        child_unifier = unify(a_child, b_child, previous)
        if isnothing(child_unifier)
            return nothing
        else
            previous = child_unifier
        end
    end
    return child_unifier
end

end # unification