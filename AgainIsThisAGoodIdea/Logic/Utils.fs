module AITools.Logic.Utils

open AITools.Logic.Core
open System.Collections.Immutable
open FSharp.Reflection

let ConstExpr = Constant >> Const
let VarExpr = Variable >> Var

(* 
    TODO this only works for two nested levels (e.g. [a; [b]]), 
    but gives compilation error with three or more (e.g. [a; [b; [c;]]]), 
    I should probably switch to a parsing function or reflection on tuples
*)
let rec makeExpr (expression: obj seq) =
    let converter (item: obj) =
        match item with
        | :? Expression as e -> e
        | :? Variable as v -> Var v
        | :? Constant as c -> Const c
        | :? (seq<obj>) as s -> makeExpr s
        | _ -> Wrap item

    expression
    |> Seq.map converter
    |> ImmutableArray.CreateRange
    |> Expr

/// Makes an expression from a tuple of expressions/other tuples, using reflection
let rec makeExpr' expr: Expression =
    let t = expr.GetType()

    if FSharpType.IsTuple t then
        expr
        |> FSharpValue.GetTupleFields
        |> Array.map makeExpr'
        |> ImmutableArray.CreateRange
        |> Expr
    else
        (expr) :?> Expression

let make lang symbolType =
    let identifier = Identifier(lang, lang.GetNext())
    symbolType (identifier, None)

let makeNamed lang symbolType name =
    let identifier = Identifier(lang, lang.GetNext())
    symbolType (identifier, Some name)

let makeMany lang symbolType n = 
    List.init n (fun _ -> make lang symbolType)

let makeManyNamed lang symbolType names =
    List.map (makeNamed lang symbolType) names

type KeyedSource<'key, 'item when 'key: comparison>(maker) =
    let mutable existing = Map.empty

    let makeForKey (key) =
        let res = maker key
        existing <- existing.Add(key, res)
        res

    member _.Get(key: 'key): 'item = 
        existing.TryFind key |> Option.defaultWith (fun () -> makeForKey key)

    member this.Item with get(key) = this.Get(key)


/// <summary>
/// Renews the variables in an expression, returning another expression 
/// where each variable has been uniformly replaced by a completely new one,
/// created with the given language.
/// </summary>
/// <remarks>
/// Replacements preserve the original variables' names.
/// </remarks>
let renewVariables language expression =
    let mutable variableMapping = Map.empty

    let rec inner expr =
        match expr with
        | Var v -> 
            let makeVar () =
                match v with
                | Variable (_, Some name) -> makeNamed language Variable name
                | Variable (_, None) -> make language Variable
            let result = variableMapping.TryFind v |> Option.defaultWith (fun () -> makeVar ())
            variableMapping <- variableMapping.Add(v, result)
            Var result
        | Expr arr->
            arr |> Seq.map inner |> ImmutableArray.CreateRange |> Expr
        | _ ->
            expr

    (inner expression), variableMapping

/// <summary>
/// Normalizes the variables in an expression, returning another expression 
/// where each variable has been uniformly replaced by a completely new one,
/// obtained by the given variable source with the "order of encounter" as the key.
/// </summary>
/// <remarks>
/// Replacements are all anonymous (names are not preserved).
/// The main purpose of this function is to allow handling of expressions 
/// which only differ by "uniform variable replacement" (i.e. each variable in an expression
/// corresponds to exactly one variable in the other).
/// </remarks>
let normalizeVariables (variableSource: KeyedSource<_,_>) expression=
    let mutable variableMapping = Map.empty

    let rec inner expr =
        match expr with
        | Var v -> 
            let makeVar () = variableSource.Get(variableMapping.Count)
            let result = variableMapping.TryFind v |> Option.defaultWith (fun () -> makeVar ())
            variableMapping <- variableMapping.Add(v, result)
            Var result
        | Expr arr->
            arr |> Seq.map inner |> ImmutableArray.CreateRange |> Expr
        | _ ->
            expr

    (inner expression), variableMapping

/// <summary>
/// Retrieves all variables in an expression.
/// Multiple occurrences of the same variable will be returned multiple times
/// </summary>
let rec allVariablesIn expression =
    match expression with
    | Var v -> seq {v}
    | Expr children -> Seq.collect allVariablesIn children
    | _ -> Seq.empty

/// <summary>
/// Maps all variables in an expression using their names as the key
/// Homonymous variables are not allowed, but the same variable can be repeated.
/// Anonymous variables are not allowed.
/// </summary>
let mapVariablesByName expression =
    let mutable result = Map.empty

    let tryAddVariable v = 
        match v with
        | Variable (_, Some name) -> 
            match result.TryFind name with
            | None -> result <- result.Add (name, v)
            | Some otherV when v = otherV -> ()
            | _ -> failwithf "Duplicate variable name \"%s\" in expression %s" name <| expression.ToString()
        | Variable (_, None) -> failwith "Anonymous variables are not allowed"

    (allVariablesIn expression) |> Seq.iter tryAddVariable 

    result