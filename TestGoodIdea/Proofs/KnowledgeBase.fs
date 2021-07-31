module Tests.Proofs.KnowledgeBase

open AITools.Proofs.KnowledgeBase
open AITools.Storage.Implementations.Dummy
open AITools.Logic.Utils
open AITools.Utils.AsyncTools
open AITools.Logic.Language
open AITools.Logic.Core
open AITools.Proofs.Components.Provers
open AITools.Proofs.Components.Base
open Xunit

// TODO this test is a placeholder, I'll have to port all the python ones
[<Fact>]
let ``A KnowledgeBase can make a proof`` () =
    let bufferSize = 1
    let storage = DummyExpressionStorage()
    let knowledgeBase = KnowledgeBase(storage)
    
    let lang = Language()

    let [IsMultipleOf3; IsMultipleOf5; IsMultipleOf15] = makeManyNamed lang ConstExpr ["IsMultipleOf3"; "IsMultipleOf5"; "IsMultipleOf15"]

    // 45 should have 2 proofs
    let isMultipleOf3a (input: {| N: int |}) = 
        input.N / 5 <= 9 && input.N % 3 = 0

    let isMultipleOf3b (input: {| N: int |}) = 
        input.N / 5 >= 9 && input.N % 3 = 0

    let isMultipleOf5 (input: {| N: int |}) = 
        input.N % 5 = 0

    let isMultipleOf15 (input: {| N: int; kb: KnowledgeBase |}) return' = async {
        let isAlsoMultipleOf3 = makeExpr' (IsMultipleOf3, Wrap input.N)
        let isAlsoMultipleOf5 = makeExpr' (IsMultipleOf5, Wrap input.N)
        do! foreachResultParallel bufferSize (input.kb.AsyncProve (isAlsoMultipleOf3, false)) <| fun p1 -> async {
            do! foreachResultParallel bufferSize (input.kb.AsyncProve(isAlsoMultipleOf5, false)) <| fun p2 -> async {
                do! return' (true, seq{p1;p2})
            }    
        }
    }

    let x = makeNamed lang VarExpr "N"

    let prover3a =
        makeProver
        <| HandlerDescriptor.MakeMapUnwrapped(makeExpr' (IsMultipleOf3, x), Predicate isMultipleOf3a, true, HandlerSafety.Safe)

    let prover3b =
        makeProver
        <| HandlerDescriptor.MakeMapUnwrapped(makeExpr' (IsMultipleOf3, x), Predicate isMultipleOf3b, true, HandlerSafety.Safe)

    let prover5 =
        makeProver
        <| HandlerDescriptor.MakeMapUnwrapped(makeExpr' (IsMultipleOf5, x), Predicate isMultipleOf5, true, HandlerSafety.Safe)

    let prover15 =
        makeProver
        <| HandlerDescriptor.MakeMapUnwrapped(makeExpr' (IsMultipleOf15, x), AsyncSourcePremisedPredicate isMultipleOf15, true, HandlerSafety.Safe, passContextAs="kb")


    let expression = makeExpr' (IsMultipleOf15, Wrap 45)

    knowledgeBase.AddProver(prover3a)
    knowledgeBase.AddProver(prover3b)
    knowledgeBase.AddProver(prover5)
    knowledgeBase.AddProver(prover15)
    let proofs = knowledgeBase.Prove(expression, false)

    Assert.Equal(Seq.length proofs, 2)
