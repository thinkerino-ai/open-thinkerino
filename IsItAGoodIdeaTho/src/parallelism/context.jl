module context
using Base.Threads: @spawn, threadid

function actually_6(proof_channel, x)
    if x == 6
        put!(proof_channel, (:actually_6, threadid()))
    end
end

function multiple_of_6(proof_channel, x)
    for p1 in prove(:multiple_of_2, x), p2 in prove(:multiple_of_3, x)
        put!(proof_channel, (p1, :and, p2) => (:multiple_of_6, threadid()))
    end
end
function multiple_of_2_a(proof_channel, x)
    if (x + 2) % 2 == 0
        put!(proof_channel, (:multiple_of_2_a, threadid()))
    end
end
function multiple_of_2_b(proof_channel, x)
    if (x - 2) % 2 == 0
        put!(proof_channel, (:multiple_of_2_b, threadid()))
    end
end

function multiple_of_3_a(proof_channel, x)
    if (x + 3) % 3 == 0
        put!(proof_channel, (:multiple_of_3_a, threadid()))
    end
end

function multiple_of_3_b(proof_channel, x)
    if (x - 3) % 3 == 0
        put!(proof_channel, (:multiple_of_3_b, threadid()))
    end
end

function set_provers(provers)
    task_local_storage("provers", provers)
end

function prove(predicate, argument)
    results = Channel()
    provers = task_local_storage("provers")
    # I wonder how I will handle this in a multi-process setting, but I guess it's a problem for my future self :P
    @async begin 
        @sync for prover in get(provers, predicate, ())
            @spawn begin
                task_local_storage("provers", provers)
                prover(results, argument)
            end
        end
        close(results)
    end
    
    return results
end

# we set the provers for the current task
set_provers(Dict(
    :multiple_of_6 => (multiple_of_6, actually_6),
    :multiple_of_2 => (multiple_of_2_a, multiple_of_2_b),
    :multiple_of_3 => (multiple_of_3_a, multiple_of_3_b),
))


end # module