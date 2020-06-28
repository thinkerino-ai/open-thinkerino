module AITools.Logic.Utils

open AITools.Logic.Core

let ConstExpr = Constant >> Const
let VarExpr = Variable >> Var

let rec makeExpr (expression: obj seq) =
    let converter (item: obj) =
        match item with
        | :? Expression as e -> e
        | :? seq<obj> as s -> makeExpr s
        | _ -> Wrap item
    expression |> Seq.map converter |> Array.ofSeq |> Expr

let make lang symbolType =
    let identifier = Identifier(lang, lang.GetNext())
    symbolType(identifier, None)

let makeNamed lang symbolType name =
    let identifier = Identifier(lang, lang.GetNext())
    symbolType(identifier, Some name)
