module AITools.Logic.Core

open AITools.Logic.Language

type Identifier = Identifier of Language * int64

type Variable = 
    | Variable of Identifier * name: string option
    
    override this.ToString() =
        match this with
        | Variable(Identifier(_, seqId), Some name) -> sprintf "?%s%i" name seqId
        | Variable(Identifier(_, seqId), None) -> sprintf "?v%i" seqId
type Constant = 
    | Constant of Identifier * name: string option

    override this.ToString() =
        match this with
        | Constant(Identifier(_, seqId), Some name) -> sprintf "%s%i" name seqId
        | Constant(Identifier(_, seqId), None) -> sprintf "o%i" seqId

type Expression = 
    | Const of Constant
    | Var of Variable
    | Wrapper of obj
    | Complex of Expression array

    member this.Contains (otherExpr: Expression) = 
        match this with
        | _ when this = otherExpr -> true
        | Complex arr -> arr |> Array.exists (fun el -> el.Contains(otherExpr))
        | _ -> false

    override this.ToString() =
        match this with
        | Const c -> c.ToString()
        | Var v -> v.ToString()
        | Wrapper o -> sprintf "{%O}" o
        | Complex arr -> arr |> Array.map string |> String.concat ", " |> sprintf "(%s)"
