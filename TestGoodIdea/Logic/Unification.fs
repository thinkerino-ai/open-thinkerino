module Tests.Logic.Unification

open AITools.Logic.Language
open AITools.Logic.Unification
open AITools.Logic.Utils
open AITools.Logic.Core
open Xunit
open System

[<Fact>]
let ``Headed binding representation works correctly`` () =
    let lang = Language(Guid("abc00000-0000-0000-0000-000000000042"), true)
    let x = makeNamed lang Variable "x"
    let y = makeNamed lang Variable "y"
    let a = makeNamed lang Constant "a"
    let b = makeNamed lang Constant "b"

    let e = makeExpr [ a; b ]

    let binding = Binding(set [ x; y ], Some e)
    
    Assert.Equal("{?x.1-abc, ?y.2-abc -> (a.3-abc, b.4-abc)}", string binding)

[<Fact>]
let ``Headless binding representation works correctly`` () =
    let lang = Language(Guid("abc00000-0000-0000-0000-000000000042"), true)
    let x = makeNamed lang Variable "x"
    let y = makeNamed lang Variable "y"

    let binding = Binding(set [ x; y ], None)

    Assert.Equal("{?x.1-abc, ?y.2-abc -> _}", string binding)


[<Fact>]
let ``Substitution representation works correctly`` () =
    let lang = Language(Guid("abc00000-0000-0000-0000-000000000042"), true)

    let x = makeNamed lang Variable "x"
    let y = makeNamed lang Variable "y"
    let z = makeNamed lang Variable "z"

    let a = makeNamed lang ConstExpr "a"

    let subst =
        Substitution
            ([ Binding(set [ x; y ], Some a)
               Binding(set [ z ], None) ])

    Assert.Equal("[{?x.1-abc, ?y.2-abc -> a.4-abc}, {?z.3-abc -> _}]", string subst)

[<Fact>]
let ``Recursive substitutions are impossible`` () =
    let lang = Language()

    let x = makeNamed lang Variable "x"
    let a = makeNamed lang Constant "a"

    let e = makeExpr [ x; a ]

    Assert.Throws<System.ArgumentException>(fun () -> Substitution([ Binding(set [ x ], Some e) ]) :> obj)
    |> ignore

[<Fact>]
let ``Substitutions are applied recursively`` () =
    let lang = Language()

    let x = makeNamed lang Variable "x"
    let y = makeNamed lang Variable "y"

    let a = makeNamed lang ConstExpr "a"
    let b = makeNamed lang ConstExpr "b"
    let c = makeNamed lang ConstExpr "c"

    let s =
        Substitution
            ([ Binding(set [ y ], Some b)
               Binding(set [ x ], Some(makeExpr [ a; y ])) ])

    let expected = makeExpr [ a; b ]

    Assert.Equal(expected, s.ApplyTo(Var x))

[<Fact>]
let ``Different constants do not unify`` () =
    let lang = Language()
    let a = makeNamed lang ConstExpr "a"
    let b = makeNamed lang ConstExpr "b"

    Assert.Equal(None, Substitution.Unify(a, b))


[<Fact>]
let ``Equal expressions unify`` () =
    let lang = Language()
    let a = makeNamed lang ConstExpr "a"
    let b = makeNamed lang ConstExpr "b"
    let c = makeNamed lang ConstExpr "c"
    let d = makeNamed lang ConstExpr "d"

    let e1 = makeExpr [ a; [ b; c ]; d ]
    let e2 = makeExpr [ a; [ b; c ]; d ]

    let expected = Substitution([])

    Assert.Equal(Some expected, Substitution.Unify(e1, e2))



[<Fact>]
let ``Different expressions do not unify`` () =
    let lang = Language()
    let a = makeNamed lang ConstExpr "a"
    let b = makeNamed lang ConstExpr "b"
    let c = makeNamed lang ConstExpr "c"
    let d = makeNamed lang ConstExpr "d"

    let e1 = makeExpr [ a; [ b; c ]; d ]
    let e2 = makeExpr [ a; [ b; c ]; a ]

    Assert.Equal(None, Substitution.Unify(e1, e2))


[<Fact>]
let ``Complex unifiable expression actually do unify`` () =
    let lang = Language()
    let v1 = makeNamed lang Variable "v1"
    let v2 = makeNamed lang Variable "v2"

    let a = makeNamed lang ConstExpr "a"
    let b = makeNamed lang ConstExpr "b"
    let c = makeNamed lang ConstExpr "c"
    let d = makeNamed lang ConstExpr "d"

    let exprD = makeExpr [ d ]

    let e1 = makeExpr [ a; [ b; c ]; exprD ]

    let e2 = makeExpr [ a; [ Var v1; c ]; v2 ]

    let expected =
        Substitution
            ([ Binding(set [ v1 ], Some b)
               Binding(set [ v2 ], Some exprD) ])

    Assert.Equal(Some expected, Substitution.Unify(e1, e2))

[<Fact>]
let ``Unification fails when the same variable gets unified with incompatible expressions`` () =
    let lang = Language()
    let v1 = make lang Variable

    let a = makeNamed lang ConstExpr "a"
    let b = makeNamed lang ConstExpr "b"
    let c = makeNamed lang ConstExpr "c"
    let d = makeNamed lang ConstExpr "d"

    let exprD = makeExpr [ d ]

    let e1 = makeExpr [ a; [ b; c ]; exprD ]

    let e3 = makeExpr [ a; [ Var v1; c ]; v1 ]

    Assert.Equal(None, Substitution.Unify(e1, e3))

// TODO translate from Python test_unification_with_variables_success_equality
// TODO translate from Python test_unification_with_variables_failure_contained
// TODO translate from Python test_unification_with_variables_success_same_expression
// TODO translate from Python test_unification_with_previous_simple_failing
// TODO translate from Python test_unification_with_previous_success_bound_to_same_expression
// TODO translate from Python test_unification_with_previous_success_bound_to_unifiable_expressions
// TODO translate from Python test_unification_with_previous_failure_bound_to_different_expressions
// TODO translate from Python test_unification_with_previous
// TODO translate from Python test_unification_with_repeated_constants
// TODO translate from Python test_unification_weird_failing_case
