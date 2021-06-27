module AITools.Logic.Core

open AITools.Logic.Language
open System.Collections.Immutable

type Identifier = Identifier of Language * int64

type Variable = 
    | Variable of Identifier * name: string option
    
    override this.ToString() =
        match this with
        | Variable(Identifier(l, seqId), Some name) -> sprintf "?%s.%i-%s" name seqId (l.LanguageId.ToString().[..2])
        | Variable(Identifier(l, seqId), None) -> sprintf "?v%i-%s" seqId (l.LanguageId.ToString().[..2])
type Constant = 
    | Constant of Identifier * name: string option

    override this.ToString() =
        match this with
        | Constant(Identifier(l, seqId), Some name) -> sprintf "%s.%i-%s" name seqId (l.LanguageId.ToString().[..2])
        | Constant(Identifier(l, seqId), None) -> sprintf "o%i-%s" seqId (l.LanguageId.ToString().[..2])

type Expression = 
    | Const of Constant
    | Var of Variable
    | Wrap of obj
    | Expr of Expression ImmutableArray

    member this.Contains (otherExpr: Expression) = 
        match this with
        | _ when this = otherExpr -> true
        | Expr arr -> arr |> Seq.exists (fun el -> el.Contains(otherExpr))
        | _ -> false

    override this.ToString() =
        match this with
        | Const c -> string c
        | Var v -> string v
        | Wrap o -> sprintf "{%O}" o
        | Expr arr -> arr |> Seq.map string |> String.concat ", " |> sprintf "(%s)"
