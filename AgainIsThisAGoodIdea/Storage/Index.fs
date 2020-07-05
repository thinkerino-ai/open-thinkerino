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
    | KeySlice of KeyElement<'a> ImmutableArray

    override this.ToString() =
        match this with
        | KeySlice slice ->
            slice
            |> Seq.map string
            |> String.concat ", "
            |> sprintf "[%s]"

type Key<'a> =
    | Key of KeySlice<'a> ImmutableArray
    override this.ToString() =
        match this with
        | Key slices -> slices |> Seq.map string |> String.concat "\n"


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

    Key
    <| ImmutableArray.CreateRange
        (seq {
            for slice in tempRes do
                yield KeySlice <| slice.ToImmutable()
         })
