module AITools.Proofs.Components.Components

open AITools.Logic.Language
open AITools.Logic.Utils
open AITools.Utils.Logger
open FSharp.Reflection
open AITools.Logic.Unification
open AITools.Logic.Core

type HandlerSafety =
    | TotallyUnsafe = 0
    | Safe = 1

type RecordHandler<'handler> =
    { HandlerFunction: 'handler
      HandlerArguments: string array }

type BaseHandlerDescriptor<'handler> =
    { Handler: 'handler
      Expression: Expression
      IsPure: bool
      Safety: HandlerSafety }

type RawHandlerExtraArguments =
    { PassSubstitutionAs: string
      PassKnowledgeBaseAs: string option }

type MappedHandlerExtraArguments =
    { PassSubstitutionAs: string option
      PassKnowledgeBaseAs: string option }

let makeMappedHandlerDescriptor ctor (expression, handler, passSubstitutionAs, passKnowledgeBaseAs, isPure, safety) =
    ctor
    <| ({ Handler = handler
          Expression = expression
          IsPure = isPure
          Safety = safety },
        { PassSubstitutionAs = passSubstitutionAs
          PassKnowledgeBaseAs = passKnowledgeBaseAs })
// TODO clean this, like... let's make it readable
type HandlerDescriptor<'handler> =
    | Raw of BaseHandlerDescriptor<'handler> * RawHandlerExtraArguments
    | Map of BaseHandlerDescriptor<'handler> * MappedHandlerExtraArguments
    | MapUnwrapped of BaseHandlerDescriptor<'handler> * MappedHandlerExtraArguments
    | MapUnwrappedRequired of BaseHandlerDescriptor<'handler> * MappedHandlerExtraArguments
    | MapUnwrappedNoVariables of BaseHandlerDescriptor<'handler> * MappedHandlerExtraArguments
    | MapNoVariables of BaseHandlerDescriptor<'handler> * MappedHandlerExtraArguments

    // TODO these are fun and all but I don't really like how they came out
    static member MakeRaw(expression, handler: 'handler, isPure, safety, ?passSubstitutionAs, ?passKnowledgeBaseAs) =
        Raw
        <| ({ Handler = handler
              Expression = expression
              IsPure = Option.defaultValue true isPure
              Safety = safety },
            { PassSubstitutionAs = Option.defaultValue "substitution" passSubstitutionAs
              PassKnowledgeBaseAs = passKnowledgeBaseAs })

    static member MakeMap(expression, handler: 'handler, isPure, safety, ?passSubstitutionAs, ?passKnowledgeBaseAs) =
        makeMappedHandlerDescriptor Map (expression, handler, passSubstitutionAs, passKnowledgeBaseAs, isPure, safety)

    static member MakeMapUnwrapped(expression,
                                   handler: 'handler,
                                   isPure,
                                   safety,
                                   ?passSubstitutionAs,
                                   ?passKnowledgeBaseAs) =
        makeMappedHandlerDescriptor
            MapUnwrapped
            (expression, handler, passSubstitutionAs, passKnowledgeBaseAs, isPure, safety)

    static member MakeMapUnwrappedRequired(expression,
                                           handler: 'handler,
                                           isPure,
                                           safety,
                                           ?passSubstitutionAs,
                                           ?passKnowledgeBaseAs) =
        makeMappedHandlerDescriptor
            MapUnwrappedRequired
            (expression, handler, passSubstitutionAs, passKnowledgeBaseAs, isPure, safety)

    static member MakeMapUnwrappedNoVariables(expression,
                                              handler: 'handler,
                                              isPure,
                                              safety,
                                              ?passSubstitutionAs,
                                              ?passKnowledgeBaseAs) =
        makeMappedHandlerDescriptor
            MapUnwrappedNoVariables
            (expression, handler, passSubstitutionAs, passKnowledgeBaseAs, isPure, safety)

    static member MakeMapNoVariables(expression,
                                     handler: 'handler,
                                     isPure,
                                     safety,
                                     ?passSubstitutionAs,
                                     ?passKnowledgeBaseAs) =
        makeMappedHandlerDescriptor
            MapNoVariables
            (expression, handler, passSubstitutionAs, passKnowledgeBaseAs, isPure, safety)

// TODO rename and remove 'kb arg
type ArgumentExtractor =
    Expression * Substitution * obj * Map<Variable, Variable> * option<Map<string, Variable>> * seq<string> * option<string> * option<string> -> Map<string, obj>

type Component<'handler> =
    { ExtractArgsByName: ArgumentExtractor
      Language: Language
      ListenedExpression: Expression
      Handler: 'handler
      InputArgs: string seq
      VariablesByName: Map<string, Variable> option
      PassSubstitutionAs: string option
      PassKnowledgeBaseAs: string option
      IsPure: bool
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
    let convertedFunc = handler handlerFunc

    { HandlerFunction = convertedFunc
      HandlerArguments = inputArgs }


let prepareVariablesByName (expression, passSubstitutionAs: string option, passKnowledgeBaseAs: string option) =
    let result = (mapVariablesByName expression)
    if passSubstitutionAs.IsSome
       && result.ContainsKey passSubstitutionAs.Value then
        failwithf
            "Argument passSubstitutionAs conflicts with variable name \"%s\", they cannot be equal"
            passSubstitutionAs.Value
    elif passKnowledgeBaseAs.IsSome
         && result.ContainsKey passKnowledgeBaseAs.Value then
        failwithf
            "Argument passKnowledgeBaseAs conflicts with variable name \"%s\", they cannot be equal"
            passKnowledgeBaseAs.Value
    else
        result

let validateRawArgumentNames (inputArgs, passSubstitutionAs, passKnowledgeBaseAs) =
    // the handler must accept a expression, a substitution and, possibly a kb
    if not
        (Array.contains
            inputArgs
             [| set [ Some "expression"
                      Some passSubstitutionAs ]
                set [ Some "expression"
                      Some passSubstitutionAs
                      passKnowledgeBaseAs ] |]) then
        failwithf "The handler has the wrong argument names %A!" inputArgs

let validateMappedArgumentNames (inputArgs, variablesByName, passSubstitutionAs, passKnowledgeBaseAs) =
    let unlistenedArgNames =
        Array.filter (fun name ->
            not (Map.containsKey name variablesByName)
            && not
                (Array.contains
                    (Some name)
                     [| passSubstitutionAs
                        passKnowledgeBaseAs |])) inputArgs

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
                | Some binding -> preparedArgs <- Map.add arg (binding.BoundObject) preparedArgs

    preparedArgs

// TODO refactor arguments
let extractArgsByName argumentMode
                      (expression,
                       unifier,
                       knowledgeBase,
                       normalizationMapping,
                       variablesByName,
                       handlerArgs,
                       passSubstitutionAs,
                       passKnowledgeBaseAs)
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
                failwith "Unexpected variable!"
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
                | _ -> failwith "Unexpected unwrapped object") argsByName.Value
        | MapUnwrappedNoVariables _ ->
            Map.map (fun _ v ->
                match v with
                | Var _ -> failwith "Unexpected variable!"
                | Wrap o -> o
                | _ -> v :> obj) argsByName.Value


    // TODO this is a job for a maybe monad but I'm too lazy
    let argsWithMaybeSubstitution =
        match passSubstitutionAs with
        | None -> baseArgs
        | Some name -> Map.add name (unifier :> obj) baseArgs

    let argsWithMaybeKnowledgeBase =
        match passKnowledgeBaseAs with
        | None -> argsWithMaybeSubstitution
        | Some name -> Map.add name (knowledgeBase :> obj) argsWithMaybeSubstitution

    argsWithMaybeKnowledgeBase


let prepareHandler (wrapHandler: 'a -> RecordHandler<'b>) handlerArgs =
    let lang = Language()

    match handlerArgs with
    | Raw (args, extraArgs) ->
        let listenedExpression, _ = renewVariables lang args.Expression
        let preparedHandler = wrapHandler args.Handler

        let argSet =
            (preparedHandler.HandlerArguments
             |> Array.map Some
             |> set)

        validateRawArgumentNames (argSet, extraArgs.PassSubstitutionAs, extraArgs.PassKnowledgeBaseAs)

        { ExtractArgsByName = extractArgsByName handlerArgs
          Language = lang
          ListenedExpression = listenedExpression
          Handler = preparedHandler.HandlerFunction
          InputArgs = preparedHandler.HandlerArguments
          VariablesByName = None
          PassSubstitutionAs = Some extraArgs.PassSubstitutionAs
          PassKnowledgeBaseAs = extraArgs.PassKnowledgeBaseAs
          IsPure = args.IsPure
          Safety = args.Safety }
    | Map (args, extraArgs)
    | MapUnwrapped (args, extraArgs)
    | MapUnwrappedRequired (args, extraArgs)
    | MapUnwrappedNoVariables (args, extraArgs)
    | MapNoVariables (args, extraArgs) ->
        let listenedExpression, _ = renewVariables lang args.Expression
        let preparedHandler = wrapHandler args.Handler

        let variablesByName =
            prepareVariablesByName (listenedExpression, extraArgs.PassSubstitutionAs, extraArgs.PassKnowledgeBaseAs)

        debug <| sprintf "prepared variablesByName: %O" variablesByName

        validateMappedArgumentNames
            (preparedHandler.HandlerArguments,
             variablesByName,
             extraArgs.PassSubstitutionAs,
             extraArgs.PassKnowledgeBaseAs)

        { ExtractArgsByName = extractArgsByName handlerArgs
          Language = lang
          ListenedExpression = listenedExpression
          Handler = preparedHandler.HandlerFunction
          InputArgs = preparedHandler.HandlerArguments
          VariablesByName = Some variablesByName
          PassSubstitutionAs = extraArgs.PassSubstitutionAs
          PassKnowledgeBaseAs = extraArgs.PassKnowledgeBaseAs
          IsPure = args.IsPure
          Safety = args.Safety }
