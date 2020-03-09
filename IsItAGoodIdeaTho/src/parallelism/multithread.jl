module multithread
using Base.Threads: @spawn

#= 
TODO I don't like this "need-to-pass-a-channel-for-results" thing, but still... 
    I might convert it in a macro later, which could work somewhat like ResumableFunctions, but using channels:

        @prover function foo(some_arg)
            @yield 1
            @yield 2
        end

    might be converted to

        function foo(proof_channel, some_arg)
            put!(proof_channel, 1)
            put!(proof_channel, 2)
        end

    but the idea still needs a lot of work :P
=#
function actually_6(proof_channel, x)
    sleep(0.3)
    if x == 6
        put!(proof_channel, :actually_6)
    end
end

function multiple_of_6(proof_channel, x)
    for p1 in prove(:multiple_of_2, x), p2 in prove(:multiple_of_3, x)
        put!(proof_channel, (p1, :and, p2) => :multiple_of_6)
    end
end
function multiple_of_2_a(proof_channel, x)
    sleep(0.11)
    if (x + 2) % 2 == 0
        put!(proof_channel, :multiple_of_2_a)
    end
end
function multiple_of_2_b(proof_channel, x)
    sleep(0.1)
    if (x - 2) % 2 == 0
        put!(proof_channel, :multiple_of_2_b)
    end
end

function multiple_of_3_a(proof_channel, x)
    if (x + 3) % 3 == 0
        put!(proof_channel, :multiple_of_3_a)
    end
end
function multiple_of_3_b(proof_channel, x)
    if (x - 3) % 3 == 0
        put!(proof_channel, :multiple_of_3_b)
    end
end

# provers for a truth about some argument X
provers = Dict(
    :multiple_of_6 => (multiple_of_6, actually_6),
    :multiple_of_2 => (multiple_of_2_a, multiple_of_2_b),
    :multiple_of_3 => (multiple_of_3_a, multiple_of_3_b),
)

function prove(predicate, argument)
    results = Channel()
    # ahahahahahahahhaha this is amazing!!!!!!
    @async begin 
        @sync for prover in get(provers, predicate, ())
            @spawn prover(results, argument)
        end
        close(results)
    end
    
    return results
end



end # module
