module AITools.Proofs.Components.Listeners

open AITools.Proofs.Components.Base
open AITools.Proofs.Components.Provers
open AITools.Logic.Unification
open AITools.Utils.AsyncTools
open AITools.Logic.Core
open AITools.Logic.Utils

type PonderMode = Known | Prove

type Listener<'context> = Component<ListenerHandlerFunction<Map<string, obj>, 'context>, 'context>
/// A handler function for a listener
and ListenerHandlerFunction<'input, 'context> =
    /// A handler that just performs some action
    | Action of ('input -> unit)
    /// A simple handler that returns an expression
    | Deducer of ('input -> Expression option)
    /// A simple handler that returns an expression under some premises
    | PremisedDeducer of ('input -> (Expression * PonderingPremise<'context> seq) option)
    /// A simple handler that returns an expression for some substitution
    | SatisfyingDeducer of ('input -> (Expression * Substitution) option)
    /// A simple handler that returns an Expression for some substitution and some premises
    | PremisedSatisfyingDeducer of ('input -> (Expression * Substitution * PonderingPremise<'context> seq) option)
    /// A handler that asynchronously performs some action
    | AsyncAction of ('input -> Async<unit>)
    /// An async deducer
    | AsyncDeducer of ('input -> Async<Expression option>)
    /// An async PremisedDeducer
    | AsyncPremisedDeducer of ('input -> Async<(Expression * PonderingPremise<'context> seq) option>)
    /// An async SatisfyingDeducer
    | AsyncSatisfyingDeducer of ('input -> Async<(Expression * Substitution) option>)
    /// An async premised satisfying deducer
    | AsyncPremisedSatisfyingDeducer of ('input -> Async<(Expression * Substitution * PonderingPremise<'context> seq) option>)
    /// A handler returning several expression and substitution pairs
    | MultiSatisfyingDeducer of ('input -> (Expression * Substitution) seq)
    /// A handler returning several expression, substitution and premise triples
    | MultiPremisedSatisfyingDeducer of ('input -> (Expression * Substitution * PonderingPremise<'context> seq) seq)
    /// A handler that uses a data Source to return expressions
    | AsyncSourceDeducer of ('input -> Expression Source)
    /// A handler that uses a data Source to return expressions and premises
    | AsyncSourcePremisedDeducer of ('input -> (Expression * (PonderingPremise<'context> seq)) Source)
    /// A handler that uses a data Source to return several expression and substitution pairs
    | AsyncSourceSatisfyingDeducer of ('input -> (Expression * Substitution) Source)
    /// A handler that uses a data Source to return several Expression, substitution and premise triples
    | AsyncSourcePremisedSatisfyingDeducer of ('input -> (Expression * Substitution * PonderingPremise<'context> seq) Source)

and PonderingPremise<'context> =
    | TriggeringExpression of Expression
    | Pondering of Pondering<'context>
    | Proof of Proof<'context>
and Pondering<'context> =
    {
        InferenceRule: Listener<'context>
        Conclusion: Expression
        Substitution: Substitution
        Premises: PonderingPremise<'context> seq
    }

let makeListenerRecordHandler rawHandler =
    let wrapFunc ctor data =
        { HandlerArguments = data.HandlerArguments
          HandlerFunction = ctor data.HandlerFunction }

    match rawHandler with
    | Action rawHandler -> makeRecordHandler rawHandler |> wrapFunc Action
    | Deducer rawHandler -> makeRecordHandler rawHandler |> wrapFunc Deducer
    | PremisedDeducer rawHandler -> makeRecordHandler rawHandler |> wrapFunc PremisedDeducer
    | SatisfyingDeducer rawHandler -> makeRecordHandler rawHandler |> wrapFunc SatisfyingDeducer
    | PremisedSatisfyingDeducer rawHandler ->
        makeRecordHandler rawHandler
        |> wrapFunc PremisedSatisfyingDeducer
    | AsyncAction rawHandler ->
        makeRecordHandler rawHandler
        |> wrapFunc AsyncAction
    | AsyncDeducer rawHandler ->
        makeRecordHandler rawHandler
        |> wrapFunc AsyncDeducer
    | AsyncPremisedDeducer rawHandler ->
        makeRecordHandler rawHandler
        |> wrapFunc AsyncPremisedDeducer
    | AsyncSatisfyingDeducer rawHandler ->
        makeRecordHandler rawHandler
        |> wrapFunc AsyncSatisfyingDeducer
    | AsyncPremisedSatisfyingDeducer rawHandler ->
        makeRecordHandler rawHandler
        |> wrapFunc AsyncPremisedSatisfyingDeducer
    | MultiSatisfyingDeducer rawHandler ->
        makeRecordHandler rawHandler
        |> wrapFunc MultiSatisfyingDeducer
    | MultiPremisedSatisfyingDeducer rawHandler ->
        makeRecordHandler rawHandler
        |> wrapFunc MultiPremisedSatisfyingDeducer
    | AsyncSourceDeducer rawHandler ->
        makeRecordHandler rawHandler
        |> wrapFunc AsyncSourceDeducer
    | AsyncSourcePremisedDeducer rawHandler ->
        makeRecordHandler rawHandler
        |> wrapFunc AsyncSourcePremisedDeducer
    | AsyncSourceSatisfyingDeducer rawHandler ->
        makeRecordHandler rawHandler
        |> wrapFunc AsyncSourceSatisfyingDeducer
    | AsyncSourcePremisedSatisfyingDeducer rawHandler ->
        makeRecordHandler rawHandler
        |> wrapFunc AsyncSourcePremisedSatisfyingDeducer

let makeListener handlerDescriptor =
    prepareHandler makeListenerRecordHandler handlerDescriptor
    
let ponder (listener: Listener<'context>) (trigger, previousSubstitution, context: 'context) return' =
    let expression = 
        match trigger with
        | TriggeringExpression expr -> expr
        | Pondering pond -> pond.Conclusion
        | Proof proof -> proof.Conclusion
    
    // TODO remove the following if I implement hypotheses "virtually" (meaning that I embed hypotheses right in the formula being pondered)
    // if knowledge_base.is_hypothetical() and self.safety == HandlerSafety.TOTALLY_UNSAFE:
    //         raise UnsafeOperationException("Unsafe listener cannot be used in hypothetical scenarios")

    let normalizedListenedExpression, normalizationMapping =
        renewVariables listener.Language listener.ListenedExpression

    let unifier = Substitution.Unify(expression, normalizedListenedExpression, previousSubstitution)

    async {
        match unifier with
        | None -> ()
        | Some unifier ->

            let argsByName = 
                listener.ExtractArgsByName
                    (expression,
                     unifier,
                     context,
                     normalizationMapping,
                     listener.VariablesByName,
                     listener.InputArgs,
                     listener.PassSubstitutionAs,
                     listener.PassContextAs)
            
            match listener.Handler with
            | Action handler -> handler argsByName
            | Deducer handler ->
                match handler argsByName with
                | None -> ()
                | Some expr ->
                    do! return'
                            { InferenceRule = listener
                              Conclusion = unifier.ApplyTo(expr)
                              Substitution = unifier
                              Premises = [trigger] }          
            | PremisedDeducer handler ->
                match handler argsByName with
                | None -> () 
                | Some (expr, premises) ->
                    do! return'
                            { InferenceRule = listener
                              Conclusion = unifier.ApplyTo(expr)
                              Substitution = unifier
                              Premises = Seq.append [trigger] premises }
            | SatisfyingDeducer handler ->
                match handler argsByName with
                | None -> () 
                | Some (expr, substitution) ->
                    do! return'
                            { InferenceRule = listener
                              Conclusion = substitution.ApplyTo(expr)
                              Substitution = substitution
                              Premises = [trigger] }
            | PremisedSatisfyingDeducer handler ->
                match handler argsByName with
                | None -> () 
                | Some (expr, subst, premises) ->
                    do! return'
                            { InferenceRule = listener
                              Conclusion = subst.ApplyTo(expr)
                              Substitution = subst
                              Premises = Seq.append [trigger] premises }
            | AsyncAction handler -> 
                do! handler argsByName
            | AsyncDeducer handler ->
                match! handler argsByName with
                | None -> ()
                | Some expr ->
                    do! return'
                            { InferenceRule = listener
                              Conclusion = unifier.ApplyTo(expr)
                              Substitution = unifier
                              Premises = [trigger] }
            | AsyncPremisedDeducer handler ->
                match! handler argsByName with
                | None -> () 
                | Some (expr, premises) ->
                    do! return'
                            { InferenceRule = listener
                              Conclusion = unifier.ApplyTo(expr)
                              Substitution = unifier
                              Premises = Seq.append [trigger] premises }
            | AsyncSatisfyingDeducer handler ->
                match! handler argsByName with
                | None -> () 
                | Some (expr, subst) ->
                    do! return'
                            { InferenceRule = listener
                              Conclusion = subst.ApplyTo(expr)
                              Substitution = subst
                              Premises = [trigger] }
            | AsyncPremisedSatisfyingDeducer handler ->
                match! handler argsByName with
                | None -> () 
                | Some (expr, subst, premises) ->
                    do! return'
                            { InferenceRule = listener
                              Conclusion = subst.ApplyTo(expr)
                              Substitution = subst
                              Premises = Seq.append [trigger] premises }
            | MultiSatisfyingDeducer handler ->
                for expr, substitution in handler argsByName do
                    do! return'
                            { InferenceRule = listener
                              Conclusion = substitution.ApplyTo(expr)
                              Substitution = substitution
                              Premises = [trigger] }
            | MultiPremisedSatisfyingDeducer handler ->
                for expr, subst, premises in handler argsByName do
                    do! return'
                            { InferenceRule = listener
                              Conclusion = subst.ApplyTo(expr)
                              Substitution = subst
                              Premises = Seq.append [trigger] premises }
            | AsyncSourceDeducer handler ->
                do! handler argsByName (fun expr ->
                        async {    
                            do! return'
                                    { InferenceRule = listener
                                      Conclusion = unifier.ApplyTo(expr)
                                      Substitution = unifier
                                      Premises = [trigger] }          
                        })
            | AsyncSourcePremisedDeducer handler ->
                do! handler argsByName (fun (expr, premises) ->
                        async {
                            do! return'
                                    { InferenceRule = listener
                                      Conclusion = unifier.ApplyTo(expr)
                                      Substitution = unifier
                                      Premises = Seq.append [trigger] premises }
                        })
            | AsyncSourceSatisfyingDeducer handler ->
                do! handler argsByName (fun (expr, subst) ->
                        async {
                            do! return'
                                    { InferenceRule = listener
                                      Conclusion = subst.ApplyTo(expr)
                                      Substitution = subst
                                      Premises = [trigger] }
                        })
            | AsyncSourcePremisedSatisfyingDeducer handler ->
                do! handler argsByName (fun (expr, subst, premises) ->
                        async {
                            do! return'
                                    { InferenceRule = listener
                                      Conclusion = subst.ApplyTo(expr)
                                      Substitution = subst
                                      Premises = Seq.append [trigger] premises }
                        })
    }
