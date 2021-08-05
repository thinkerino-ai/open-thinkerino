module AITools.Proofs.Components.Base

open AITools.Logic.Language
open AITools.Logic.Utils
open AITools.Utils.Logger
open FSharp.Reflection
open AITools.Logic.Unification
open AITools.Logic.Core
open System

exception InvalidHandlerArgumentTypeException of string

type HandlerSafety =
    | TotallyUnsafe = 0
    | Safe = 1

type HandlerPurity =
    | Pure = 0
    | Impure = 1

type HandlerSubstitutionArgument =
    | PassSubstitutionAs of string
    | NoSubstitution

type HandlerContextArgument =
    | PassContextAs of string
    | NoContext

type RecordHandler<'handler> =
    { HandlerFunction: 'handler
      HandlerArguments: string array }

type BaseHandlerDescriptor<'handler> =
    { Handler: 'handler
      Expression: Expression
      Purity: HandlerPurity
      Safety: HandlerSafety }

type RawHandlerExtraArguments =
    { PassSubstitutionAs: HandlerSubstitutionArgument
      PassContextAs: HandlerContextArgument }

type MappedHandlerExtraArguments =
    { PassSubstitutionAs: HandlerSubstitutionArgument
      PassContextAs: HandlerContextArgument }

let makeMappedHandlerDescriptor ctor (expression, handler, passSubstitutionAs, passContextAs, purity, safety) =
    ctor
    <| ({ Handler = handler
          Expression = expression
          Purity = purity
          Safety = safety },
        { PassSubstitutionAs = passSubstitutionAs
          PassContextAs = passContextAs })
// TODO clean this, like... let's make it readable
type HandlerDescriptor<'handler> =
    | Raw of BaseHandlerDescriptor<'handler> * RawHandlerExtraArguments
    | Map of BaseHandlerDescriptor<'handler> * MappedHandlerExtraArguments
    | MapUnwrapped of BaseHandlerDescriptor<'handler> * MappedHandlerExtraArguments
    | MapUnwrappedRequired of BaseHandlerDescriptor<'handler> * MappedHandlerExtraArguments
    | MapUnwrappedNoVariables of BaseHandlerDescriptor<'handler> * MappedHandlerExtraArguments
    | MapNoVariables of BaseHandlerDescriptor<'handler> * MappedHandlerExtraArguments

    // TODO these are fun and all but I don't really like how they came out
    static member MakeRaw(expression, handler: 'handler, purity, safety, passSubstitutionAs, passContextAs) =
        Raw
        <| ({ Handler = handler
              Expression = expression
              Purity = purity
              Safety = safety },
            { PassSubstitutionAs = passSubstitutionAs
              PassContextAs = passContextAs })

    static member MakeMap(expression, handler: 'handler, purity, safety, passSubstitutionAs, passContextAs) =
        makeMappedHandlerDescriptor Map (expression, handler, passSubstitutionAs, passContextAs, purity, safety)

    static member MakeMapUnwrapped(expression,
                                   handler: 'handler,
                                   purity,
                                   safety,
                                   passSubstitutionAs,
                                   passContextAs) =
        makeMappedHandlerDescriptor
            MapUnwrapped
            (expression, handler, passSubstitutionAs, passContextAs, purity, safety)

    static member MakeMapUnwrappedRequired(expression,
                                           handler: 'handler,
                                           purity,
                                           safety,
                                           passSubstitutionAs,
                                           passContextAs) =
        makeMappedHandlerDescriptor
            MapUnwrappedRequired
            (expression, handler, passSubstitutionAs, passContextAs, purity, safety)

    static member MakeMapUnwrappedNoVariables(expression,
                                              handler: 'handler,
                                              purity,
                                              safety,
                                              passSubstitutionAs,
                                              passContextAs) =
        makeMappedHandlerDescriptor
            MapUnwrappedNoVariables
            (expression, handler, passSubstitutionAs, passContextAs, purity, safety)

    static member MakeMapNoVariables(expression,
                                     handler: 'handler,
                                     purity,
                                     safety,
                                     passSubstitutionAs,
                                     passContextAs) =
        makeMappedHandlerDescriptor
            MapNoVariables
            (expression, handler, passSubstitutionAs, passContextAs, purity, safety)


type ArgumentExtractor<'context> =
    Expression * Substitution * 'context * Map<Variable, Variable> * option<Map<string, Variable>> * seq<string> * HandlerSubstitutionArgument * HandlerContextArgument -> Map<string, obj>

type Component<'handler, 'context> =
    { ExtractArgsByName: ArgumentExtractor<'context>
      Language: Language
      ListenedExpression: Expression
      Handler: 'handler
      InputArgs: string seq
      VariablesByName: Map<string, Variable> option
      PassSubstitutionAs: HandlerSubstitutionArgument
      PassContextAs: HandlerContextArgument
      Purity: HandlerPurity
      Safety: HandlerSafety }

    override x.ToString() = x.ListenedExpression.ToString()

/// Generates a map-based handler and the list of its arguments from a record-based handler
let makeRecordHandler (handlerFunc: 'input -> 'output) =
    let inputType = typeof<'input>
    if not (FSharpType.IsRecord(inputType))
    then invalidArg "handlerFunc" "Only record types are allowed"

    let inputArgs =
        FSharpType.GetRecordFields(inputType)
        |> Array.map (fun f -> f.Name)

    let constructor =
        FSharpValue.PreComputeRecordConstructor(inputType)

    // helper to convert a Map into the 'input Record the handler accepts
    let handler func (data: Map<string, obj>) =
        let input =
            constructor (Array.map (fun f -> data.[f]) inputArgs) :?> 'input

        input |> func

    // a new handler function, which now accepts a Map and then calls the original handlerFunc
    let convertedFunc input = 
        try
            handler handlerFunc input
        with
        | :? InvalidCastException -> raise <| InvalidHandlerArgumentTypeException "Invalid argument types for record"

    { HandlerFunction = convertedFunc
      HandlerArguments = inputArgs }

// TODO this was a nice dream, but the type system didn't agree
// /// Generates a map-based handler and the list of its arguments from a record-based handler
// let makeFunctionHandler (handlerFunc:#obj -> #obj) =
//     let inputType = handlerFunc.GetType()
//     // TODO this is not really solid, is it? :P
//     let invoke = inputType.GetMethods() |> Array.find (fun m -> m.Name = "Invoke")
//     let inputArgs = invoke.GetParameters() |> Array.map (fun p -> p.Name)
//     let inputArgsList = inputArgs |> List.ofArray
//     //let boxF f (a: obj) = f <| downcast a
//     let convertedFunc (data: Map<string, obj>) =
//         let rec callWithArgs (f: obj) args = 
//             match args with
//             | [] -> f
//             | head :: tail -> 
//                 callWithArgs (downcast f <| data.[head]) tail
//         try
//             callWithArgs handlerFunc inputArgsList
//         with
//         | :? InvalidCastException -> raise <| InvalidHandlerArgumentTypeException "Invalid argument types for record"
//     { HandlerFunction = convertedFunc
//       HandlerArguments = inputArgs }


let prepareVariablesByName (expression, passSubstitutionAs, passContextAs) =
    let result = (mapVariablesByName expression)
    match passSubstitutionAs, passContextAs with
    | PassSubstitutionAs s, _ when result.ContainsKey s ->
        failwithf
            "Argument passSubstitutionAs conflicts with variable name \"%s\", they cannot be equal"
            s
    | _, PassContextAs s when result.ContainsKey s ->
        failwithf
            "Argument passContextAs conflicts with variable name \"%s\", they cannot be equal"
            s
    | _ -> result

let validateRawArgumentNames (inputArgs, passSubstitutionAs, passContextAs) =
    // the handler must accept an expression, a substitution and possibly a kb
    let inputSet = set inputArgs

    match passSubstitutionAs with 
    | NoSubstitution -> failwith "You need to specify a name for the substitution, but you didn't!"
    | PassSubstitutionAs subst -> 
        if not
            (
                Array.contains inputSet.Count [| 2; 3 |]
                && inputSet.Contains "expression"
                && inputSet.Contains subst
                && match passContextAs with
                    | PassContextAs s -> inputSet.Contains(s)
                    | NoContext -> inputSet.Count = 2
            )
        then
            let expected = 
                match passContextAs with
                | PassContextAs ctx -> ["expression"; subst; ctx]
                | NoContext -> ["expression"; subst]
            failwithf "The handler has the wrong argument names %A! expected %A" inputArgs expected


let validateMappedArgumentNames (inputArgs, variablesByName, passSubstitutionAs, passContextAs) =
    let unlistenedArgNames =
        Array.filter 
            (fun name ->
                not (Map.containsKey name variablesByName)
                && not
                    (PassSubstitutionAs name = passSubstitutionAs
                    || PassContextAs name = passContextAs)
            ) 
            inputArgs

    if not (Array.isEmpty unlistenedArgNames) then
        failwithf
            "The handler has the wrong argument names %A! Handler arguments %A are not present in the arguments"
            inputArgs
            unlistenedArgNames


// TODO this can be curried or somehow refactored
let mapSubstitutionToFunctionArgs (variablesByName: Map<_, _> option,
                                   substitution: Substitution,
                                   funcArgNames,
                                   normalizationMapping) =
    debug <| sprintf "mapSubstitutionToFunctionArgs"
    let mutable preparedArgs = Map.empty
    for arg in funcArgNames do
        debug <| sprintf "mapSubstitutionToFunctionArgs arg %s" arg
        if variablesByName.IsSome
           && Map.containsKey arg variablesByName.Value then
            match Map.tryFind (Map.find arg variablesByName.Value) normalizationMapping with
            | None -> 
                debug <| sprintf "mapSubstitutionToFunctionArgs what is happening?\n\tvariablesByName: %O\n\tfuncArgNames: %A\n\tnormalizationMapping: %O" variablesByName funcArgNames normalizationMapping
                failwith "What is happening here?"
            | Some mappedVariable ->
                match substitution.GetBoundObjectFor(mappedVariable) with
                | None -> failwithf "Variable %A is not mapped in substitution %A" mappedVariable substitution
                | Some boundObject -> preparedArgs <- Map.add arg (boundObject) preparedArgs

    preparedArgs

// TODO refactor arguments
let extractArgsByName argumentMode
                      (expression,
                       unifier,
                       context,
                       normalizationMapping,
                       variablesByName,
                       handlerArgs,
                       passSubstitutionAs,
                       passContextAs)
                      =
    debug <| sprintf "extraArgsByName"
    let argsByName =
        lazy (mapSubstitutionToFunctionArgs (variablesByName, unifier, handlerArgs, normalizationMapping))

    debug <| sprintf "extraArgsByName value = %O" argsByName.Value
    let baseArgs =
        match argumentMode with
        | Raw _ -> Map.add "expression" expression Map.empty
        | Map _ -> Map.map (fun _ v -> v :> obj) argsByName.Value
        | MapNoVariables _ ->
            if Map.exists (fun _ v ->
                match v with
                | Var _ -> true
                | _ -> false) argsByName.Value then
                raise <| InvalidHandlerArgumentTypeException "Unexpected variable!"
            else
                Map.map (fun _ v -> v :> obj) argsByName.Value
        | MapUnwrapped _ ->
            Map.map (fun _ v ->
                match v with
                | Wrap o -> o
                | _ -> v :> obj) argsByName.Value
        | MapUnwrappedRequired _ ->
            Map.map (fun _ v ->
                match v with
                | Wrap o -> o
                | _ -> raise <| InvalidHandlerArgumentTypeException "Unexpected unwrapped object") argsByName.Value
        | MapUnwrappedNoVariables _ ->
            Map.map (fun _ v ->
                match v with
                | Var _ -> raise <| InvalidHandlerArgumentTypeException "Unexpected variable!"
                | Wrap o -> o
                | _ -> v :> obj) argsByName.Value


    // TODO this is a job for a maybe monad but I'm too lazy
    let argsWithMaybeSubstitution =
        match passSubstitutionAs with
        | NoSubstitution -> baseArgs
        | PassSubstitutionAs name -> Map.add name (unifier :> obj) baseArgs

    let argsWithMaybeContext =
        match passContextAs with
        | NoContext -> argsWithMaybeSubstitution
        | PassContextAs name -> Map.add name (context :> obj) argsWithMaybeSubstitution

    argsWithMaybeContext


let prepareHandler (wrapHandler: 'a -> RecordHandler<'b>) handlerArgs =
    let lang = Language()

    match handlerArgs with
    | Raw (args, extraArgs) ->
        let listenedExpression, _ = renewVariables lang args.Expression
        let preparedHandler = wrapHandler args.Handler

        validateRawArgumentNames (preparedHandler.HandlerArguments, extraArgs.PassSubstitutionAs, extraArgs.PassContextAs)

        { ExtractArgsByName = extractArgsByName handlerArgs
          Language = lang
          ListenedExpression = listenedExpression
          Handler = preparedHandler.HandlerFunction
          InputArgs = preparedHandler.HandlerArguments
          VariablesByName = None
          PassSubstitutionAs = extraArgs.PassSubstitutionAs
          PassContextAs = extraArgs.PassContextAs
          Purity = args.Purity
          Safety = args.Safety }
    | Map (args, extraArgs)
    | MapUnwrapped (args, extraArgs)
    | MapUnwrappedRequired (args, extraArgs)
    | MapUnwrappedNoVariables (args, extraArgs)
    | MapNoVariables (args, extraArgs) ->
        let listenedExpression, _ = renewVariables lang args.Expression
        let preparedHandler = wrapHandler args.Handler

        let variablesByName =
            prepareVariablesByName (listenedExpression, extraArgs.PassSubstitutionAs, extraArgs.PassContextAs)

        debug <| sprintf "prepared variablesByName: %O" variablesByName

        validateMappedArgumentNames
            (preparedHandler.HandlerArguments,
             variablesByName,
             extraArgs.PassSubstitutionAs,
             extraArgs.PassContextAs)

        { ExtractArgsByName = extractArgsByName handlerArgs
          Language = lang
          ListenedExpression = listenedExpression
          Handler = preparedHandler.HandlerFunction
          InputArgs = preparedHandler.HandlerArguments
          VariablesByName = Some variablesByName
          PassSubstitutionAs = extraArgs.PassSubstitutionAs
          PassContextAs = extraArgs.PassContextAs
          Purity = args.Purity
          Safety = args.Safety }
