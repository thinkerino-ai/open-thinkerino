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
    | Wrap of obj
    | Expr of Expression array

    member this.Contains (otherExpr: Expression) = 
        match this with
        | _ when this = otherExpr -> true
        | Expr arr -> arr |> Seq.exists (fun el -> el.Contains(otherExpr))
        | _ -> false

    override this.ToString() =
        match this with
        | Const c -> c.ToString()
        | Var v -> v.ToString()
        | Wrap o -> sprintf "{%O}" o
        | Expr arr -> arr |> Seq.map string |> String.concat ", " |> sprintf "(%s)"
