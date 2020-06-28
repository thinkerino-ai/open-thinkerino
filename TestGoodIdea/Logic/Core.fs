module Tests.Core

open AITools.Logic.Core
open AITools.Logic.Language
open Xunit

[<Fact>]
let ``Named Constant representation works correctly`` () =
    let lang = Language()

    let c =
        Constant(Identifier(lang, lang.GetNext()), Some "foo")

    Assert.Equal("foo1", c.ToString())

[<Fact>]
let ``Unnamed Constant representation works correctly`` () =
    let lang = Language()

    let c =
        Constant(Identifier(lang, lang.GetNext()), None)

    Assert.Equal("o1", c.ToString())

[<Fact>]
let ``Named Variable representation works correctly`` () =
    let lang = Language()

    let v =
        Variable(Identifier(lang, lang.GetNext()), Some "foo")

    Assert.Equal("?foo1", v.ToString())

[<Fact>]
let ``Unnamed Variable representation works correctly`` () =
    let lang = Language()

    let v =
        Variable(Identifier(lang, lang.GetNext()), None)

    Assert.Equal("?v1", v.ToString())


[<Fact>]
let ``Int wrapper representation works correctly`` () =
    let w = Wrapper(33)

    Assert.Equal("{33}", w.ToString())


[<Fact>]
let ``String wrapper representation works correctly`` () =
    let w = Wrapper("wow")

    Assert.Equal("{wow}", w.ToString())


[<Fact>]
let ``Simple expression representation works correctly`` () =
    let lang = Language()
    let expr = Constant(Identifier(lang, lang.GetNext()), None) |> Const

    Assert.Equal("o1", expr.ToString())



[<Fact>]
let ``Complex expression representation works correctly`` () =
    let lang = Language()
    let expr = Complex [|
        Constant(Identifier(lang, lang.GetNext()), None) |> Const;
        Complex [|
            Constant(Identifier(lang, lang.GetNext()), None) |> Const;
            Constant(Identifier(lang, lang.GetNext()), None) |> Const;
        |];
        Variable(Identifier(lang, lang.GetNext()), None) |> Var;
    |]

    Assert.Equal("(o1, (o2, o3), ?v4)", expr.ToString())


[<Fact>]
let ``Expression.Contains returns true when the expression contains a Variable`` () =
    let lang = Language()
    let element = Variable(Identifier(lang, lang.GetNext()), None) |> Var;

    let expr = Complex [|
        Constant(Identifier(lang, lang.GetNext()), None) |> Const;
        Complex [|
            Constant(Identifier(lang, lang.GetNext()), None) |> Const;
            element;
            Constant(Identifier(lang, lang.GetNext()), None) |> Const;
        |];
        Variable(Identifier(lang, lang.GetNext()), None) |> Var;
    |]

    Assert.True(expr.Contains(element))


[<Fact>]
let ``Expression.Contains returns true when the expression contains a Constant`` () =
    let lang = Language()
    let element = Constant(Identifier(lang, lang.GetNext()), None) |> Const;

    let expr = Complex [|
        Constant(Identifier(lang, lang.GetNext()), None) |> Const;
        Complex [|
            Constant(Identifier(lang, lang.GetNext()), None) |> Const;
            element;
            Constant(Identifier(lang, lang.GetNext()), None) |> Const;
        |];
        Variable(Identifier(lang, lang.GetNext()), None) |> Var;
    |]

    Assert.True(expr.Contains(element))




[<Fact>]
let ``Expression.Contains returns true when the expression contains a Wrapper`` () =
    let lang = Language()
    let element = Wrapper("foo")

    let expr = Complex [|
        Constant(Identifier(lang, lang.GetNext()), None) |> Const;
        Complex [|
            Constant(Identifier(lang, lang.GetNext()), None) |> Const;
            element;
            Constant(Identifier(lang, lang.GetNext()), None) |> Const;
        |];
        Variable(Identifier(lang, lang.GetNext()), None) |> Var;
    |]

    Assert.True(expr.Contains(element))


[<Fact>]
let ``Expression.Contains returns true when the expression contains another Expression`` () =
    let lang = Language()
    let element = Complex [|
        Constant(Identifier(lang, lang.GetNext()), None) |> Const;
        Constant(Identifier(lang, lang.GetNext()), None) |> Const;
    |]

    let expr = Complex [|
        Constant(Identifier(lang, lang.GetNext()), None) |> Const;
        Complex [|
            Constant(Identifier(lang, lang.GetNext()), None) |> Const;
            element;
            Constant(Identifier(lang, lang.GetNext()), None) |> Const;
        |];
        Variable(Identifier(lang, lang.GetNext()), None) |> Var;
    |]

    Assert.True(expr.Contains(element))