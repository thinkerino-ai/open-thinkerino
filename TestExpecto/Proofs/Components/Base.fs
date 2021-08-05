module Thinkerino.Tests.Proofs.Components.Base
open Expecto
open AITools.Proofs.Components.Base

[<Tests>]
let testsMakeFunctionHandler= testList "makeRecordHandler tests" [
    test "when called correctly wraps the original function and extracts its arguments" {
        let foo (input:{|a:_; b:_; c:_;|}) = input.a + input.b * input.c

        let handler = makeRecordHandler foo

        let inputMap = Map.ofList ["a", 2:>obj; "b", 3:>obj; "c", 4:>obj]
        Expect.sequenceEqual handler.HandlerArguments ["a"; "b"; "c"] "the arguments should be a, b and c"
        Expect.equal (handler.HandlerFunction inputMap) 14 "passing a map to the handler function should return the result of the original function"
    }
]