module Thinkerino.Tests.Proofs.Listeners
#nowarn "25"

open AITools.Proofs.Language
open AITools.Proofs.Components.Provers
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


let listenerTestMakers = [
    
]

[<Tests>]
let tests = 
    listenerTestMakers
    |> runWithKb
    |> testList "listners"