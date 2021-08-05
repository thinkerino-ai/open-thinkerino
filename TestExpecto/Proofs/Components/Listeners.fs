module Thinkerino.Tests.Proofs.Components.Listeners
open System.Collections.Generic
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
    fun testKb -> test "if there are multiple listeners for a formula, all of their results are returned" { 
        let language = Language()
        let v = VarExprSource language
        let c = ConstExprSource language
        
        
        let IsA, Meows, Purrs, cat, dylan = c?IsA, c?Meows, c?Purrs, c?cat, c?dylan


        let catsMeow (input:{|cat: _|}) =
            Some Meows.[input.cat]
        let catsPurr (input:{|cat: _|}) =
            Some Purrs.[input.cat]

        let listenedExpression = IsA.[v?cat, cat]
        let meowListener = 
            makeListener
            <| HandlerDescriptor.MakeMap (listenedExpression, Deducer catsMeow, HandlerPurity.Pure, HandlerSafety.Safe, NoSubstitution, NoContext)
        let purrListener = 
            makeListener
            <| HandlerDescriptor.MakeMap (listenedExpression, Deducer catsPurr, HandlerPurity.Pure, HandlerSafety.Safe, NoSubstitution, NoContext)

        testKb.AddListener meowListener
        testKb.AddListener purrListener

        // TODO this should be part of the KB tests
        Expect.sequenceEqual 
            (testKb.GetListenersFor(listenedExpression)) 
            [meowListener; purrListener] 
            "the listeners are correctly associated to the listened formula"

        let conclusions = testKb.Ponder [IsA.[dylan, cat]] |> List.ofSeq

        Expect.hasLength conclusions 2 "there are exactly 2 conclusions"
        

        Expect.sequenceEqual 
            (conclusions |> Seq.map (fun c -> c.Conclusion))
            [Meows.[dylan]; Purrs.[dylan]]
            "the conclusions should be that dylan meows and purrs"
        
        Expect.all
            conclusions
            (fun c -> 
                [
                    for p in c.Premises do
                        match p with
                        | TriggeringExpression e -> e
                        | Pondering pond -> pond.Conclusion
                        | Proof proof -> proof.Conclusion
                ] = [ IsA.[dylan, cat] ])
            "the conclusions are based on the fact that dylan is a cat"
    }

    // TODO this should be a kb test
    fun testKb -> test "adding the same listener twice doesn't result in a duplicate" {
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
        testKb.AddListener listener

        Expect.sequenceEqual 
            (testKb.GetListenersFor listenedExpression)
            [listener]
            "only one instance of the listener is retrieved"
    }
    fun testKb -> test "if multiple expressions are pondered on, all the results are returned" { 
        let language = Language()
        let v = VarExprSource language
        let c = ConstExprSource language
        
        let IsA, Meows, cat, dylan, hugo = c?IsA, c?Meows, c?cat, c?dylan, c?hugo

        let catsMeow (input:{|cat: _|}) =
            Some Meows.[input.cat]

        let listenedExpression = IsA.[v?cat, cat]
        let listener = 
            makeListener
            <| HandlerDescriptor.MakeMap (listenedExpression, Deducer catsMeow, HandlerPurity.Pure, HandlerSafety.Safe, NoSubstitution, NoContext)

        testKb.AddListener listener

        let conclusions = testKb.Ponder [IsA.[dylan, cat]; IsA.[hugo, cat]] |> List.ofSeq

        Expect.hasLength conclusions 2 "there are exactly 2 conclusions"
        
        Expect.containsAll 
            (conclusions |> Seq.map (fun c -> c.Conclusion))
            [Meows.[dylan]; Meows.[hugo]]
            "the conclusions should be that dylan and hugo meow"

        Expect.containsAll
            (conclusions |> Seq.map(fun c -> c.Premises |> List.ofSeq) |> HashSet)
            (HashSet [[TriggeringExpression IsA.[dylan, cat]]; [TriggeringExpression IsA.[hugo, cat]]])
            "the conclusions are based on the fact that dylan and hugo are cats"
    }
    fun testKb -> test "a listener can return a sequence of results" { 
        let language = Language()
        let v = VarExprSource language
        let c = ConstExprSource language
        
        
        let IsA, Meows, Purrs, cat, dylan = c?IsA, c?Meows, c?Purrs, c?cat, c?dylan


        let catsMeowAndPurr (input:{|cat: _|}) = seq{
            yield Meows.[input.cat]
            yield Purrs.[input.cat]
        }

        let listenedExpression = IsA.[v?cat, cat]
        let listener = 
            makeListener
            <| HandlerDescriptor.MakeMap (listenedExpression, MultiDeducer catsMeowAndPurr, HandlerPurity.Pure, HandlerSafety.Safe, NoSubstitution, NoContext)

        testKb.AddListener listener

        let conclusions = testKb.Ponder [IsA.[dylan, cat]] |> List.ofSeq

        Expect.hasLength conclusions 2 "there are exactly 2 conclusions"
        

        Expect.sequenceEqual 
            (conclusions |> List.map(fun c -> c.Conclusion))
            [Meows.[dylan]; Purrs.[dylan]]
            "the conclusions should be that dylan meows and purrs"
        Expect.allEqual
            (conclusions |> List.map(fun c -> c.Premises |> List.ofSeq))
            [TriggeringExpression IsA.[dylan, cat]]
            "the conclusions are based on the fact that dylan is a cat"
    }
]

[<Tests>]
let tests = 
    listenerTestMakers
    |> runWithKb
    |> testList "listners"