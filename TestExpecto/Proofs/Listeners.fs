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
    fun testKb -> test "side-effect only listeners are run during pondering" { 
            let language = Language()
            let v = VarExprSource language
            let c = ConstExprSource language
            
            
            let Is, Meows, cat, dylan = c?Is, c?Meows, c?cat, c?dylan

            let mutable calls = []

            let catsMeow (input:{|cat: _|}) =
                calls <- input.cat :: calls

            let listenedExpression = Is.[v?cat, cat]
            let listener = 
                makeListener
                <| HandlerDescriptor.MakeMap (listenedExpression, Action catsMeow, HandlerPurity.Pure, HandlerSafety.Safe)

            testKb.AddListener listener

            let proofs = testKb.Ponder [Is.[dylan, cat]] |> List.ofSeq

            Expect.hasLength proofs 0 "no proofs should have been found"
            Expect.equal calls [dylan] "the calls should include only dylan"
        }
]

[<Tests>]
let tests = 
    listenerTestMakers
    |> runWithKb
    |> testList "listners"