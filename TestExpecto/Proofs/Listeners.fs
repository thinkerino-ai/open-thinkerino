module Thinkerino.Tests.Proofs.Listeners
#nowarn "25"

open AITools.Proofs.Language
open AITools.Proofs.Components.Listeners
open Microsoft.FSharp.Core.LanguagePrimitives
open AITools.Proofs.Components.Base
open AITools.Utils.AsyncTools
open Thinkerino.Tests.Utils

open AITools.Storage.Base
open AITools.Storage.Implementations.Dummy
open Expecto
open AITools.Proofs.KnowledgeBase
open AITools.Logic.Language
open AITools.Logic.Core
open AITools.Logic.Utils
open AITools.Proofs.Builtin.Provers


let listenerTestMakers: (KnowledgeBase -> Test) list = [
    fun testKb -> test "a listener can return no results" { 
            let language = Language()
            let v = VarExprSource language
            let c = ConstExprSource language
            
            let IsA, cat, dylan = c?IsA, c?cat, c?dylan

            let mutable calls = []

            let catsMeow (input:{|cat: _|}) =
                calls <- input.cat :: calls

            let listenedExpression = IsA.[v?cat, cat]
            let listener = 
                makeListener
                <| HandlerDescriptor.MakeMap (listenedExpression, Action catsMeow, HandlerPurity.Pure, HandlerSafety.Safe, NoSubstitution, NoContext)

            testKb.AddListener listener

            let conclusions = testKb.Ponder [IsA.[dylan, cat]] |> List.ofSeq

            Expect.hasLength conclusions 0 "no conclusions should have been found"
            Expect.equal calls [dylan] "the calls should include only dylan"
        }
    fun testKb -> test "a listener can return a single simple result" { 
            let language = Language()
            let v = VarExprSource language
            let c = ConstExprSource language
            
            
            let IsA, Meows, cat, dylan = c?IsA, c?Meows, c?cat, c?dylan


            let catsMeow (input:{|cat: _|}) =
                Some Meows.[input.cat]

            let listenedExpression = IsA.[v?cat, cat]
            let listener = 
                makeListener
                <| HandlerDescriptor.MakeMap (listenedExpression, Deducer catsMeow, HandlerPurity.Pure, HandlerSafety.Safe, NoSubstitution, NoContext)

            testKb.AddListener listener

            let conclusions = testKb.Ponder [IsA.[dylan, cat]] |> List.ofSeq

            Expect.hasLength conclusions 1 "there is exactly 1 conclusion"
            
            let conclusion = conclusions.Head

            Expect.equal conclusion.Conclusion Meows.[dylan] "the conclusion should be that dylan meows"
            Expect.equal 
                [
                    for p in conclusion.Premises do
                        match p with
                        | TriggeringExpression e -> e
                        | Pondering pond -> pond.Conclusion
                        | Proof proof -> proof.Conclusion
                ]
                [ IsA.[dylan, cat] ]
                "the conclusion is based on the fact that dylan is a cat"
        }
]

[<Tests>]
let tests = 
    listenerTestMakers
    |> runWithKb
    |> testList "listners"