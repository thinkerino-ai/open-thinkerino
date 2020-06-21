module AITools.Logic.Language

open System.Threading


type Language(languageId, enabled) =
    let nextId = ref 0L

    member this.LanguageId = languageId
    member this.GetNext() = if enabled then Interlocked.Increment(nextId) else failwith "nope"
    
    override this.GetHashCode() = hash languageId
    override this.Equals(other) = 
        match other with
        | :? Language as l -> languageId = l.LanguageId
        | _ -> false

    override this.ToString() = languageId |> sprintf "Language(%A)"

    new() = Language(System.Guid.NewGuid(), true)