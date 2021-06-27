module Tests.Logic.Core
#nowarn "25"

open AITools.Logic.Core
open AITools.Logic.Language
open Xunit
open AITools.Logic.Utils

[<Fact>]
let ``Named Constant representation works correctly`` () =
    let lang = Language()

    let c = makeNamed lang Constant "foo"

    Assert.Equal("foo1", string c)

[<Fact>]
let ``Unnamed Constant representation works correctly`` () =
    let lang = Language()

    let c = make lang Constant

    Assert.Equal("o1", string c)

[<Fact>]
let ``Named Variable representation works correctly`` () =
    let lang = Language()

    let v = makeNamed lang Variable "foo"

    Assert.Equal("?foo1", string v)

[<Fact>]
let ``Unnamed Variable representation works correctly`` () =
    let lang = Language()

    let v = make lang Variable

    Assert.Equal("?v1", string v)


[<Fact>]
let ``Int wrapper representation works correctly`` () =
    let w = Wrap(33)

    Assert.Equal("{33}", string w)


[<Fact>]
let ``String wrapper representation works correctly`` () =
    let w = Wrap("wow")

    Assert.Equal("{wow}", string w)


[<Fact>]
let ``Simple expression representation works correctly`` () =
    let lang = Language()
    let expr = make lang ConstExpr

    Assert.Equal("o1", string expr)

[<Fact>]
let ``Complex expression representation works correctly`` () =
    let lang = Language()

    let [a; b; c] = makeMany lang ConstExpr 3
    let x = make lang VarExpr

    let expr = makeExpr' (a, (b,c), x)

    Assert.Equal("(o1, (o2, o3), ?v4)", string expr)


[<Fact>]
let ``Expression.Contains returns true when the expression contains a Variable`` () =
    let lang = Language()
    let element = make lang VarExpr

    let [a; b; c] = makeMany lang ConstExpr 3
    let x = make lang VarExpr

    let expr = makeExpr' (a, (b, element, c), x)

    Assert.True(expr.Contains(element))


[<Fact>]
let ``Expression.Contains returns true when the expression contains a Constant`` () =
    let lang = Language()

    let element = make lang ConstExpr

    let [a; b; c] = makeMany lang ConstExpr 3
    let x = make lang VarExpr

    let expr = makeExpr' (a, (b, element, c), x)

    Assert.True(expr.Contains(element))


[<Fact>]
let ``Expression.Contains returns true when the expression contains a Wrapper`` () =
    let lang = Language()
    let element = Wrap "foo"

    let [a; b; c] = makeMany lang ConstExpr 3
    let x = make lang VarExpr

    let expr = makeExpr' (a, (b, element, c), x)

    Assert.True(expr.Contains(element))


[<Fact>]
let ``Expression.Contains returns true when the expression contains another Expression`` () =
    let lang = Language()

    let [a'; b'] = makeMany lang ConstExpr 2
    let element = makeExpr [a'; b']

    let [a; b; c] = makeMany lang ConstExpr 3
    let x = make lang VarExpr

    let expr = makeExpr' (a, (b, (a', b'), c), x)

    Assert.True(expr.Contains(element))

// TODO move these to its own test file?
[<Fact>]
let ``makeAuto can build a single Variable correctly`` () = 
    let lang = Language()

    let a = makeAuto lang Variable

    Assert.IsType<Variable> a

[<Fact>]
let ``makeAuto can build a single VarExpr correctly`` () = 
    let lang = Language()

    let a = makeAuto lang VarExpr

    Assert.IsAssignableFrom<Expression> a

[<Fact>]
let ``makeAuto can build multiple Variables correctly`` () = 
    let lang = Language()

    let a, b, c = makeAuto lang Variable

    let _: Variable = a
    let _: Variable = b
    let _: Variable = c

    ignore <| Assert.IsType<Variable> a
    ignore <| Assert.IsType<Variable> b
    ignore <| Assert.IsType<Variable> c

[<Fact>]
let ``makeAuto can build multiple VarExpr correctly`` () = 
    let lang = Language()

    let a, b, c = makeAuto lang VarExpr

    let _: Expression = a
    let _: Expression = b
    let _: Expression = c

    ignore <| Assert.IsAssignableFrom<Expression> a
    ignore <| Assert.IsAssignableFrom<Expression> b
    ignore <| Assert.IsAssignableFrom<Expression> c
