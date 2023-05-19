module Thinkerino.Logic.Language
open Fable.Core

[<AttachMembers>]
type Language(languageId, enabled) =
    let nextId = ref 0L
    let lockObj = obj ()

    member this.LanguageId = languageId

    member this.GetNext() =
        if enabled then
            lock lockObj (fun () ->
                let res = nextId.Value
                nextId.Value <- nextId.Value + 1L
                res)
        else
            failwith "Disabled languages cannot generate ids anymore"

    new() = Language(System.Guid.NewGuid(), true)

    override this.ToString() = languageId |> sprintf "Language(%A)"

    override this.GetHashCode() = hash languageId

    override this.Equals(other) =
        match other with
        | :? Language as l -> languageId = l.LanguageId
        | _ -> false

    interface System.IComparable with
        member x.CompareTo y =
            match y with
            | :? Language as y ->
                x
                    .LanguageId
                    .ToString()
                    .CompareTo(y.LanguageId.ToString())
            | _ ->
                raise
                <| System.ArgumentException("Cannot compare instances of different types")
