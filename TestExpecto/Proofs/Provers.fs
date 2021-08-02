module Thinkerino.Tests.Proofs.Provers
open AITools.Proofs.Language

#nowarn "25"

open AITools.Storage.Base
open AITools.Storage.Implementations.Dummy
open Expecto
open AITools.Proofs.KnowledgeBase
open AITools.Logic.Language
open AITools.Logic.Utils
open AITools.Proofs.Builtin.Provers

let storageImplementations: list<_ * (unit -> ExpressionStorage)> = [
    nameof DummyExpressionStorage, fun () -> upcast new DummyExpressionStorage()
    nameof DummyIndexedExpressionStorage, fun () -> upcast new DummyIndexedExpressionStorage()
]


let testWithImplementation (name, impl: unit -> ExpressionStorage) =
    let setupImplementation test () =
            use storage = impl()
            let kb = KnowledgeBase(storage)
            test kb

    testFixture setupImplementation [
        "we can retrieve known expressions", 
            fun testKb -> 
                let language = Language()
                let [IsA; dylan; cat] = makeManyNamed language ConstExpr ["IsA"; "dylan"; "cat"]
                let expr = makeExpr' (IsA, dylan, cat)
                testKb.AddExpression expr

                let proofs = testKb.Prove (expr, retrieveOnly=true) |> List.ofSeq

                Expect.hasLength proofs 1 "should have one proof"
                Expect.all 
                    proofs
                    (fun p -> p.Conclusion = expr)
                    "the conclusion should be the expression"
        // TODO test_retrieve_known_expression_transactional
        // TODO test_retrieve_known_expression_rollback
        "we can retrieve known open expressions", 
            fun testKb -> 
                let language = Language()
                let v = VarExprSource language
                let [IsA; dylan; cat; hugo] = makeManyNamed language ConstExpr ["IsA"; "dylan"; "cat"; "hugo"]

                let dylanIsACat = makeExpr' (IsA, dylan, cat)
                let hugoIsACat = makeExpr' (IsA, hugo, cat)
                testKb.AddExpressions <| seq {
                    dylanIsACat
                    hugoIsACat
                }

                let query = makeExpr' (IsA, v.["x"], cat)
                let proofs = testKb.Prove (query, retrieveOnly=true) |> List.ofSeq

                Expect.hasLength proofs 2 "should have two proofs"
                Expect.exists 
                    proofs
                    (fun p -> p.Conclusion = dylanIsACat)
                    "it should be known that dylan is a cat"
                Expect.exists 
                    proofs
                    (fun p -> p.Conclusion = hugoIsACat)
                    "it should be known that hugo is a cat"

        "open expressions are added only once",
            fun testKb ->
                let language = Language()
                let v = VarExprSource language

                let [Foo; a; b] = makeManyNamed language ConstExpr ["Foo"; "a"; "b"]
                
                testKb.AddExpressions <| seq {
                    makeExpr' (Foo, a, b)
                    makeExpr' (Foo, v.["x"], v.["y"])
                    makeExpr' (Foo, v.["x"], v.["x"])
                    // the following expression is not added, because it normalizes the same as the second expression
                    makeExpr' (Foo, v.["w"], v.["z"])
                }

                Expect.equal (testKb.Size) 3 "there should be three items"
        
        "expressions are normalized, so the same variables can be reused in axioms",
            fun testKb ->
                let language = Language()
                let v = VarExprSource language
                let [Foo; Bar; Baz; a; b] = makeManyNamed language ConstExpr ["Foo"; "Bar"; "Baz"; "a"; "b"]

                testKb.AddProver RestrictedModusPonens

                testKb.AddExpressions <| seq {
                    makeExpr' (Foo, a, b)
                    makeExpr' (Implies, (Foo, v.["x"], v.["y"]), (Bar, v.["x"]))
                    makeExpr' (Implies, (Bar, v.["y"]), (Baz, v.["y"]))
                }

                let query = makeExpr' (Baz, a)
                let proofs = testKb.Prove (query, retrieveOnly=false) |> List.ofSeq

                Expect.isNonEmpty proofs "there is at least a proof"

    ]
    |> List.ofSeq
    |> testList name

[<Tests>]
let tests = 
    storageImplementations 
    |> List.map testWithImplementation
    |> testList "provers"