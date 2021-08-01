module Thinkerino.Tests.Logic.Core

#nowarn "25"

open Expecto
open Expecto.Flip
open AITools.Logic.Language
open AITools.Logic.Utils
open AITools.Logic.Core
open System


[<Tests>]
let tests =
    testList
        "core module"
        [ test "Named Constant representation works correctly" {
            let lang =
                Language(Guid("abc00000-0000-0000-0000-000000000042"), true)

            let c = makeNamed lang Constant "foo"

            string c
            |> Expect.equal "the constant is rendered correctly" "foo.1-abc"
          }
          test "Unnamed Constant representation works correctly" {
              let lang =
                  Language(Guid("abc00000-0000-0000-0000-000000000042"), true)

              let c = make lang Constant

              string c
              |> Expect.equal "c renders to o1-abc" "o1-abc"
          }
          test "Named Variable representation works correctly" {
              let lang =
                  Language(Guid("abc00000-0000-0000-0000-000000000042"), true)

              let v = makeNamed lang Variable "foo"

              string v
              |> Expect.equal "v renders to ?foo.1-abc" "?foo.1-abc"
          }
          test "Unnamed Variable representation works correctly" {
              let lang =
                  Language(Guid("abc00000-0000-0000-0000-000000000042"), true)

              let v = make lang Variable

              string v
              |> Expect.equal "v renders to ?v1-abc" "?v1-abc"

          }
          test "Int wrapper representation works correctly" {
              let w = Wrap(33)

              string w
              |> Expect.equal "w renders to {33}" "{33}"
          }
          test "String wrapper representation works correctly" {
              let w = Wrap("wow")

              string w
              |> Expect.equal "w renders to {wow}" "{wow}"

          }
          test "Simple expression representation works correctly" {
              let lang =
                  Language(Guid("abc00000-0000-0000-0000-000000000042"), true)

              let expr = make lang ConstExpr

              string expr
              |> Expect.equal "expr renders to o1-abc" "o1-abc"
          }
          test "Complex expression representation works correctly" {
              let lang =
                  Language(Guid("abc00000-0000-0000-0000-000000000042"), true)

              let [ a; b; c ] = makeMany lang ConstExpr 3
              let x = make lang VarExpr
              let expr = makeExpr' (a, (b, c), x)

              string expr
              |> Expect.equal "expr renders to the correct string" "(o1-abc, (o2-abc, o3-abc), ?v4-abc)"

          }
          test "Expression.Contains returns true when the expression contains a Variable" {
              let lang = Language()
              let element = make lang VarExpr
              let [ a; b; c ] = makeMany lang ConstExpr 3
              let x = make lang VarExpr
              let expr = makeExpr' (a, (b, element, c), x)

              expr.Contains(element)
              |> Expect.isTrue "expr contains its sub-expression"

          }
          test "Expression.Contains returns true when the expression contains a Constant" {
              let lang = Language()
              let element = make lang ConstExpr
              let [ a; b; c ] = makeMany lang ConstExpr 3
              let x = make lang VarExpr
              let expr = makeExpr' (a, (b, element, c), x)


              expr.Contains(element)
              |> Expect.isTrue "expr contains its sub-expression"

          }
          test "Expression.Contains returns true when the expression contains a Wrapper" {
              let lang = Language()
              let element = Wrap "foo"
              let [ a; b; c ] = makeMany lang ConstExpr 3
              let x = make lang VarExpr
              let expr = makeExpr' (a, (b, element, c), x)

              expr.Contains(element)
              |> Expect.isTrue "expr contains its sub-expression"

          }
          test "Expression.Contains returns true when the expression contains another Expression" {
              let lang = Language()
              let [ a'; b' ] = makeMany lang ConstExpr 2
              let element = makeExpr [ a'; b' ]
              let [ a; b; c ] = makeMany lang ConstExpr 3
              let x = make lang VarExpr
              let expr = makeExpr' (a, (b, (a', b'), c), x)

              expr.Contains(element)
              |> Expect.isTrue "expr contains element"
          } ]
