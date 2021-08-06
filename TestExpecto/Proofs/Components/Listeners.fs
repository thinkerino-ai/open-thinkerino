module Thinkerino.Tests.Proofs.Components.Listeners
open System.Collections.Generic
open AITools.Logic.Unification
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


let listenerTestMakers (setup: (KnowledgeBase -> unit) -> unit) = [
    test "a listener can return no results" { 
        setup <| fun testKb -> 
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
    test "a listener can return a single simple result" { 
        setup <| fun testKb -> 
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
                        | TriggeringExpression (e, _) -> e
                        | Pondering pond -> pond.Conclusion
                        | Proof proof -> proof.Conclusion
                ]
                [ IsA.[dylan, cat] ]
                "the conclusion is based on the fact that dylan is a cat"
        }
    test "if there are multiple listeners for a formula, all of their results are returned" { 
        setup <| fun testKb -> 
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
            
            Expect.containsAll 
                (conclusions |> Seq.map (fun c -> c.Conclusion))
                [Meows.[dylan]; Purrs.[dylan]]
                "the conclusions should be that dylan meows and purrs"
            
            Expect.all
                conclusions
                (fun c -> 
                    [
                        for p in c.Premises do
                            match p with
                            | TriggeringExpression (e, _) -> e
                            | Pondering pond -> pond.Conclusion
                            | Proof proof -> proof.Conclusion
                    ] = [ IsA.[dylan, cat] ])
                "the conclusions are based on the fact that dylan is a cat"
        }

        // TODO this should be a kb test
    test "adding the same listener twice doesn't result in a duplicate" {
        setup <| fun testKb -> 
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
    test "if multiple expressions are pondered on, all the results are returned" { 
        setup <| fun testKb -> 
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
                (HashSet [
                    [TriggeringExpression (IsA.[dylan, cat], Substitution.Empty)]; 
                    [TriggeringExpression (IsA.[hugo, cat], Substitution.Empty)]])
                "the conclusions are based on the fact that dylan and hugo are cats"
        }
    test "a listener can return a sequence of results" { 
        setup <| fun testKb -> 
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
                [TriggeringExpression (IsA.[dylan, cat], Substitution.Empty)]
                "the conclusions are based on the fact that dylan is a cat"
        }
    test "if a listener returns premises, they are included in the result" { 
        setup <| fun testKb -> 
            let bufferSize = 1
            let language = Language()
            let v = VarExprSource language
            let c = ConstExprSource language
            
            let IsA, Meows, SomeDumbTruth, SomeOtherDumbTruth, cat, dylan = c?IsA, c?Meows, c?SomeDumbTruth, c?SomeOtherDumbTruth, c?cat, c?dylan

            let catsMeow (input: {|cat: _; kb: KnowledgeBase|}) return' = async {
                do! foreachResult bufferSize (input.kb.AsyncProve(SomeDumbTruth, false)) <| fun proof ->
                    foreachResult bufferSize (input.kb.AsyncProve(SomeOtherDumbTruth, false)) <| fun otherProof ->
                        return' (Meows.[input.cat], seq {Proof proof; Proof otherProof})
            }

            let listenedExpression = IsA.[v?cat, cat]
            let listener = 
                makeListener
                <| HandlerDescriptor.MakeMap (listenedExpression, AsyncSourcePremisedDeducer catsMeow, HandlerPurity.Pure, HandlerSafety.Safe, NoSubstitution, PassContextAs "kb")

            testKb.AddListener listener
            testKb.AddExpressions [SomeDumbTruth; SomeOtherDumbTruth]

            let conclusions = testKb.Ponder [IsA.[dylan, cat]] |> List.ofSeq

            Expect.hasLength conclusions 1 "there is exactly 1 conclusion"
            
            let conclusion = conclusions.Head

            Expect.equal conclusion.Conclusion Meows.[dylan] "the conclusion should be that dylan meows"

            Expect.hasLength conclusion.Premises 3 "the conclusion has 3 premises"

            Expect.exists
                conclusion.Premises
                (function 
                | TriggeringExpression (e, _) when e = IsA.[dylan, cat] -> true 
                | _ -> false)
                "the triggering expression is part of the premises"
            Expect.exists
                conclusion.Premises
                (function 
                | Proof {Conclusion = e} when e = SomeDumbTruth -> true 
                | _ -> false)
                "the first additional premise returned by the listener expression is part of the premises"
            Expect.exists
                conclusion.Premises
                (function 
                | Proof {Conclusion = e} when e = SomeOtherDumbTruth -> true 
                | _ -> false)
                "the second additional premise returned by the listener expression is part of the premises"
        }
    test "if a listener returns substitutions, they override the original one" { 
        setup <| fun testKb -> 
            (* note: I don't why I added this back in Python, but I think it's due to the following thought:
                "if a component returns substitutions, it should perform the merge internally, if it doesn't, I trust it"
                for an example, see RestrictedModusPonens, which passes the input substitution to the recursive `prove` call
            *)
            let language = Language()
            let v = VarExprSource language
            let c = ConstExprSource language
            
            let IsA, Meows, Purrs, cat, dylan = c?IsA, c?Meows, c?Purrs, c?cat, c?dylan

            let someSubstitution = Substitution.Empty
            let someOtherSubstitution = Substitution.Empty

            let catsMeowAndPurr (input:{|cat: _|}) = seq{
                yield Meows.[input.cat], someSubstitution
                yield Purrs.[input.cat], someOtherSubstitution
            }

            let listenedExpression = IsA.[v?cat, cat]
            let listener = 
                makeListener
                <| HandlerDescriptor.MakeMap (listenedExpression, MultiSatisfyingDeducer catsMeowAndPurr, HandlerPurity.Pure, HandlerSafety.Safe, NoSubstitution, NoContext)

            testKb.AddListener listener

            let conclusions = testKb.Ponder [IsA.[dylan, cat]] |> List.ofSeq

            Expect.hasLength conclusions 2 "there are exactly 2 conclusions"

            Expect.sequenceEqual 
                (conclusions |> List.map(fun c -> c.Conclusion))
                [Meows.[dylan]; Purrs.[dylan]]
                "the conclusions should be that dylan meows and purrs"
            Expect.allEqual
                (conclusions |> List.map(fun c -> c.Premises |> List.ofSeq))
                [TriggeringExpression (IsA.[dylan, cat], Substitution.Empty)]
                "the conclusions are based on the fact that dylan is a cat"
            Expect.sequenceEqual
                (conclusions |> List.map(fun c -> c.Substitution))
                [someSubstitution; someOtherSubstitution]
                "the listener's conclusions have overridden the actual ones"
        }
    test "listeners can be chained" { 
        setup <| fun testKb -> 
            let language = Language()
            let v = VarExprSource language
            let c = ConstExprSource language
            
            let A, B, C, D, foo = c?A, c?B, c?C, c?D, c?foo

            let deduceFromAB (input: {|x: _|}) =
                Some B.[input.x]
            let deduceFromBC (input: {|x: _|}) =
                Some C.[input.x]
            let deduceFromCD (input: {|x: _|}) =
                Some D.[input.x]
            
            [
                A.[v?x], deduceFromAB
                B.[v?x], deduceFromBC
                C.[v?x], deduceFromCD
            ]
            |>List.map (
                fun (expr, handler) -> HandlerDescriptor.MakeMap (expr, Deducer handler, HandlerPurity.Pure, HandlerSafety.Safe, NoSubstitution, NoContext)
                >> makeListener
                >> testKb.AddListener
            )
            |> ignore

            let conclusions = testKb.Ponder [A.[foo]] |> List.ofSeq

            Expect.hasLength conclusions 3 "there are exactly 3 conclusions"
            
            Expect.containsAll
                (conclusions |> List.map (fun c -> c.Conclusion))
                [B.[foo]; C.[foo]; D.[foo]]
                "we conclude B(foo), C(foo) and D(foo)"
    }
]

[<Tests>]
let listenerTests =
    listenerTestMakers
    |> runWithKb
    |> testList "listeners"