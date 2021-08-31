module Thinkerino.Tests.Utils

open Thinkerino.Storage.Base
open Thinkerino.Storage.Implementations.Dummy
open Thinkerino.Proofs.KnowledgeBase
open Expecto

exception SomeException

let storageImplementations: list<_ * (unit -> ExpressionStorage)> = [
    nameof DummyExpressionStorage, fun () -> upcast new DummyExpressionStorage()
    nameof DummyIndexedExpressionStorage, fun () -> upcast new DummyIndexedExpressionStorage()
]

let runWithKb tests = [
    for name, makeStorage in storageImplementations do
        let provideKb makeTest =
            use storage = makeStorage()
            let kb = KnowledgeBase(storage)
            makeTest kb
        yield tests provideKb
        |> testList $"with storage: {name}"
]