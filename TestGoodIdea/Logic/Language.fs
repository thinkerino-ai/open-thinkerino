module Tests

open AITools.Logic.Language
open Xunit

[<Fact>]
let ``Language generates sequential ids`` () =
    let language = Language()

    Assert.Equal(language.GetNext(), 1L)
    Assert.Equal(language.GetNext(), 2L)
    Assert.Equal(language.GetNext(), 3L)
