module core

export LogicObject, Constant, Variable, Expression

abstract type LogicObject end

# TODO thread safety!
let last_id = 0
    struct Constant <: LogicObject
        id::Tuple{Val{Constant},Int}
        Constant() = new((Val(Constant), last_id += 1))
    end
    
    struct Variable <: LogicObject
        id::Tuple{Val{Variable},Int}
        Variable() = new((Val(Variable), last_id += 1))
    end

    struct Expression <: LogicObject
        id::Tuple{Val{Expression},Int}
        children::AbstractArray{<:LogicObject}
        Expression(children) = new((Val(Expression), last_id += 1), children)
    end
end

appears_in(obj::LogicObject, other::LogicObject) = false
appears_in(obj::LogicObject, other::Expression) = any(obj == child || appears_in(obj, child) for child in other.children)

end # core