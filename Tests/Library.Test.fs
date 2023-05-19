module Thinkerino.Library

open Expecto
open Thinkerino.Say
open Expecto.Flip

[<Tests>]
let tests =
  testList "foo" [
    testCase "foo1" <| fun _ ->
      let res = hello "gigi"
      Expect.equal "Should be equal" "Hello gigi" res
  ]