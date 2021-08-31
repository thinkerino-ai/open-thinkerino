module Thinkerino.Tests.Main
open Expecto
open Thinkerino.Tests.Proofs.Components.Provers
open Thinkerino.Tests.Proofs.Components.Listeners
open Thinkerino.Tests.Logic.Core
open Thinkerino.Tests.Logic.Language
open Tests.Logic.Unification
open Thinkerino.Tests.Proofs.Components.Base

[<EntryPoint>]
let main argv =
    let allTests = testList "allTests" [
        for i = 0 to 0 do
            yield testList $"iteration-{i}" [
                coreTests
                languageTests
                unificationTests
                makeRecordHandlerTests
                proverTests
                listenerTests
            ]
    ]
    runTestsWithCLIArgs [] [||] allTests
