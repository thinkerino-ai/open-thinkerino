module Tests.Logic.Unification

open AITools.Logic.Language
open AITools.Logic.Unification
open AITools.Logic.Utils
open AITools.Logic.Core
open Xunit

[<Fact>]
let ``recursive substitutions are impossible`` () =
    let language = Language()

    let x = makeNamed language Variable "x"
    let a = makeNamed language Constant "a"

    let e = makeExpr [ x; a ]

    Assert.Throws<System.ArgumentException>(fun () -> Substitution([ Binding(set [ x ], Some e) ]) :> obj)
    |> ignore

[<Fact>]
let ``substitutions are applied recursively`` () =
    let language = Language()

    let x = makeNamed language Variable "x"
    let y = makeNamed language Variable "y"

    let a = makeNamed language ConstExpr "a"
    let b = makeNamed language ConstExpr "b"
    let c = makeNamed language ConstExpr "c"

    let s =
        Substitution
            ([ Binding(set [ y ], Some b)
               Binding(set [ x ], Some(makeExpr [ a; y ])) ])

    let expected = makeExpr [ a; b ]

    Assert.Equal(expected, s.ApplyTo(Var x))
