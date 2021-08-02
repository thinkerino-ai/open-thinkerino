module AITools.Storage.Implementations.Dummy

open AITools.Storage.Index
open System.Collections.Generic
open AITools.Storage.Base
open AITools.Logic.Core
open AITools.Logic.Unification

type DummyExpressionStorage() =
    inherit ExpressionStorage()

    let objects = HashSet()

    override _.Add(expressions: seq<Expression>): unit = 
        for expr in expressions do
            objects.Add(expr) |> ignore

    override _.SearchUnifiable(expression: Expression): seq<Expression * Substitution> = seq {
            for expr in objects do
                let unifier = Substitution.Unify(expr, expression)
                match unifier with
                | Some subst -> yield expr, subst
                | None -> ()
        }

    override _.Size with get () = objects.Count

    override _.Dispose () = ()

type DummyTrieIndex<'keyItem, 'item when 'keyItem: equality>() =
    inherit TrieIndex<'keyItem, 'item>()

    let mutable subindices: Dictionary<KeyElement<'keyItem>, TrieIndex<'keyItem, 'item>> = Dictionary()
    let objects = HashSet()

    override _.MaybeStoreObject(object) = objects.Add(object) |> ignore

    override _.GetOrCreateSubindex(keyElement) =
        if not (subindices.ContainsKey(keyElement))
        then subindices.Add(keyElement, DummyTrieIndex<_, _>())

        subindices.[keyElement]


    override _.Objects = seq objects

    override _.Subindices = subindices |> Seq.map (fun kvp -> kvp.Value)

    override _.KeysAndSubindices =
        subindices
        |> Seq.map (fun kvp -> (kvp.Key, kvp.Value))

    override _.GetSubindexByKeyElement(keyElement) = 
        if subindices.ContainsKey(keyElement) 
        then Some <| subindices.[keyElement]
        else None

type DummyAbstruseIndex<'keyItem, 'item when 'keyItem: equality>() =
    inherit AbstruseIndex<'keyItem, 'item, DummyAbstruseIndex<'keyItem, 'item>>()

    let objects = HashSet()

    let subindexTree = DummyTrieIndex<_, _>()

    override _.MakeNode() = DummyAbstruseIndex()
    override _.Objects = seq objects
    override _.MaybeStoreObject(object) = objects.Add(object) |> ignore
    override _.SubindexTree = upcast subindexTree

type DummyIndexedExpressionStorage() =
    inherit ExpressionStorage()

    let objects = DummyAbstruseIndex()

    override _.Add(expressions) = 
        for expr in expressions do
            let key = makeKey expr
            objects.Add(key, expr)

    override _.SearchUnifiable(expression) = seq {
            let key = makeKey(expression)
            for expr in objects.Retrieve(key) do
                let unifier = Substitution.Unify(expr, expression)
                match unifier with
                | Some subst -> yield expr, subst
                | None -> ()
        }

    override _.Size with get () = 
        Key.Wildcard 
        |> objects.Retrieve 
        |> Seq.length

    override _.Dispose () = ()