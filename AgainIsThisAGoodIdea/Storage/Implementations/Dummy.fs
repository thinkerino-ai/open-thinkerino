module AITools.Storage.Implementations.Dummy

open AITools.Storage.Index

type DummyTrieIndex<'keyItem, 'item when 'keyItem: comparison and 'item: comparison>() =
    inherit TrieIndex<'keyItem, 'item>()

    let mutable subindices: Map<KeyElement<'keyItem>, TrieIndex<'keyItem, 'item>> = Map.empty
    let mutable objects = Set.empty

    override _.MaybeStoreObject(object) = objects <- objects.Add object

    override _.GetOrCreateSubindex(keyElement) =
        if not (subindices.ContainsKey(keyElement))
        then subindices <- subindices.Add(keyElement, DummyTrieIndex<_, _>())

        subindices.[keyElement]


    override _.Objects = seq objects

    override _.Subindices = subindices |> Seq.map (fun kvp -> kvp.Value)

    override _.KeysAndSubindices =
        subindices
        |> Seq.map (fun kvp -> (kvp.Key, kvp.Value))

    override _.GetSubindexByKeyElement(keyElement) = subindices.TryFind(keyElement)

type DummyAbstruseIndex<'keyItem, 'item when 'keyItem: comparison and 'item: comparison>() =
    inherit AbstruseIndex<'keyItem, 'item, DummyAbstruseIndex<'keyItem, 'item>>()

    let mutable objects = Set.empty

    let subindexTree = DummyTrieIndex<_, _>()

    override _.MakeNode() = DummyAbstruseIndex()
    override _.Objects = seq objects
    override _.MaybeStoreObject(object) = objects <- objects.Add(object)
    override _.SubindexTree = upcast subindexTree


    interface System.IComparable with
        member this.CompareTo(other) =
            match other with
            | :? DummyAbstruseIndex<'keyItem, 'item> as otherIndex -> compare (hash this) (hash otherIndex)
            | _ -> failwith "cannot compare an AbstruseIndex with other types"
