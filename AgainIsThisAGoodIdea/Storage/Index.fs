module AITools.Storage.Index

open AITools.Logic.Core
open System.Collections.Immutable


type KeyElement<'a> =
    | Wildcard
    | Further of int
    | Literal of 'a

    override this.ToString() =
        match this with
        | Wildcard -> "*"
        | Further n -> string n
        | Literal x -> x.ToString()

type KeySlice<'a> =
    { Elements: KeyElement<'a> ImmutableArray }

    override this.ToString() =
        this.Elements
        |> Seq.map string
        |> String.concat ", "
        |> sprintf "[%s]"

type Key<'a> =
    { Slices: KeySlice<'a> ImmutableArray }
    override this.ToString() =
        this.Slices
        |> Seq.map string
        |> String.concat "\n"


let makeKey expr =
    let tempRes =
        ResizeArray<ImmutableArray.Builder<Expression KeyElement>>()

    let rec inner (expr, level) =
        if tempRes.Count = level
        then tempRes.Add(ImmutableArray.CreateBuilder<Expression KeyElement>())

        match expr with
        | Expr children ->
            tempRes.[level].Add(Further children.Length)
            for child in children do
                inner (child, level + 1)
        | Var _ -> tempRes.[level].Add(Wildcard)
        | _ -> tempRes.[level].Add(Literal expr)

    inner (expr, 0)

    { Slices =
          ImmutableArray.CreateRange
              (seq {
                  for slice in tempRes do
                      yield { Elements = slice.ToImmutable() }
               }) }

[<AbstractClass>]
type TrieIndex<'keyItem, 'item> =
    member this.Add(key: Key<'keyItem>, obj: 'item, ?level: int) =
        let level =
            match level with
            | None -> 0
            | Some i -> i

        raise <| System.NotImplementedException()

    abstract MaybeStoreObject: 'item -> unit
    abstract GetOrCreateSubindex: KeyElement<'keyItem> -> TrieIndex<'keyItem, 'item>
    abstract GetAllObjects: unit -> seq<'item>
    abstract GetAllSubindices: unit -> seq<TrieIndex<'keyItem, 'item>>
    abstract GetAllKeysAndSubindices: unit -> seq<KeyElement<'keyItem> * TrieIndex<'keyItem, 'item>>
    abstract GetSubindexByKeyElement: KeyElement<'keyItem> -> TrieIndex<'keyItem, 'item> option
