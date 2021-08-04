module AITools.Proofs.Components.Provers

open AITools.Proofs.Components.Base
open AITools.Logic.Core
open AITools.Logic.Unification
open AITools.Logic.Utils
open AITools.Utils.AsyncTools
open AITools.Utils.Logger


type Prover<'context> = Component<ProverHandlerFunction<Map<string, obj>, 'context>, 'context>
/// A handler function for a prover
and ProverHandlerFunction<'input, 'context> =
    /// A simple handler that returns a boolean
    | Predicate of ('input -> bool)
    /// A simple handler that maybe returns a boolean
    | MaybePredicate of ('input -> bool option)
    /// A simple handler that returns a boolean under some premises
    | PremisedPredicate of ('input -> bool * Proof<'context> seq)
    /// A simple handler that returns a boolean for some substitution
    | Satisfier of (((((('input -> bool * Substitution))))))
    /// A simple handler that returns a boolean for some substitution and some premises
    | PremisedSatisfier of (((((('input -> bool * Substitution * Proof<'context> seq))))))
    /// An async predicate
    | AsyncPredicate of ('input -> Async<bool>)
    /// An async MaybePredicate
    | AsyncMaybePredicate of ('input -> Async<bool option>)
    /// An async PremisedPredicate
    | AsyncPremisedPredicate of ('input -> Async<bool * Proof<'context> seq>)
    /// An async satisfier
    | AsyncSatisfier of ('input -> Async<bool * Substitution>)
    /// An async premised satisfier
    | AsyncPremisedSatisfier of ('input -> Async<bool * Substitution * Proof<'context> seq>)
    /// A handler returning several boolean and substitution pairs
    | MultiSatisfier of ('input -> (bool * Substitution) seq)
    /// A handler returning several boolean, substitution and premise triples
    | MultiPremisedSatisfier of ('input -> (bool * Substitution * Proof<'context> seq) seq)
    /// A handler that uses a data Source to return booleans
    | AsyncSourcePredicate of ('input -> bool Source)
    /// A handler that uses a data Source to return booleans and premises
    | AsyncSourcePremisedPredicate of ('input -> (bool * (Proof<'context> seq)) Source)
    /// A handler that uses a data Source to return several boolean and substitution pairs
    | AsyncSourceSatisfier of ('input -> (bool * Substitution) Source)
    /// A handler that uses a data Source to return several boolean, substitution and premise triples
    | AsyncSourcePremisedSatisfier of ('input -> (bool * Substitution * Proof<'context> seq) Source)


and Proof<'context> =
    { InferenceRule: Prover<'context>
      Conclusion: Expression
      Substitution: Substitution
      Premises: Proof<'context> seq }

    override this.ToString() =
        sprintf "%s \n-> %O (%O)" (this.Premises |> Seq.map string |> String.concat " and ") this.Conclusion this.InferenceRule

// TODO I think this could become an active pattern (never used them but sounds like that kind of thing :P)
let makeProverRecordHandler rawHandler =
    let wrapFunc ctor data =
        { HandlerArguments = data.HandlerArguments
          HandlerFunction = ctor data.HandlerFunction }

    match rawHandler with
    | Predicate rawHandler -> makeRecordHandler rawHandler |> wrapFunc Predicate
    | MaybePredicate rawHandler -> makeRecordHandler rawHandler |> wrapFunc MaybePredicate
    | PremisedPredicate rawHandler -> makeRecordHandler rawHandler |> wrapFunc PremisedPredicate
    | Satisfier rawHandler -> makeRecordHandler rawHandler |> wrapFunc Satisfier
    | PremisedSatisfier rawHandler ->
        makeRecordHandler rawHandler
        |> wrapFunc PremisedSatisfier
    | AsyncPredicate rawHandler ->
        makeRecordHandler rawHandler
        |> wrapFunc AsyncPredicate
    | AsyncMaybePredicate rawHandler ->
        makeRecordHandler rawHandler
        |> wrapFunc AsyncMaybePredicate
    | AsyncPremisedPredicate rawHandler ->
        makeRecordHandler rawHandler
        |> wrapFunc AsyncPremisedPredicate
    | AsyncSatisfier rawHandler ->
        makeRecordHandler rawHandler
        |> wrapFunc AsyncSatisfier
    | AsyncPremisedSatisfier rawHandler ->
        makeRecordHandler rawHandler
        |> wrapFunc AsyncPremisedSatisfier
    | MultiSatisfier rawHandler ->
        makeRecordHandler rawHandler
        |> wrapFunc MultiSatisfier
    | MultiPremisedSatisfier rawHandler ->
        makeRecordHandler rawHandler
        |> wrapFunc MultiPremisedSatisfier
    | AsyncSourcePredicate rawHandler ->
        makeRecordHandler rawHandler
        |> wrapFunc AsyncSourcePredicate
    | AsyncSourcePremisedPredicate rawHandler ->
        makeRecordHandler rawHandler
        |> wrapFunc AsyncSourcePremisedPredicate
    | AsyncSourceSatisfier rawHandler ->
        makeRecordHandler rawHandler
        |> wrapFunc AsyncSourceSatisfier
    | AsyncSourcePremisedSatisfier rawHandler ->
        makeRecordHandler rawHandler
        |> wrapFunc AsyncSourcePremisedSatisfier

let makeProver handlerDescriptor =
    prepareHandler makeProverRecordHandler handlerDescriptor


let prove (prover: Prover<'context>) (expression, previousSubstitution, context: 'context) return' =
    // TODO remove the following if I implement hypotheses "virtually" (meaning that I embed hypotheses right in the expression being proven)
    // if knowledge_base.is_hypothetical() and self.safety == HandlerSafety.TOTALLY_UNSAFE:
    //     raise UnsafeOperationException("Unsafe prover cannot be used in hypothetical scenarios")
    let normalizedListenedExpression, normalizationMapping =
        renewVariables prover.Language prover.ListenedExpression

    let unifier =
        Substitution.Unify(expression, normalizedListenedExpression, previousSubstitution)

    async {
        try
            match unifier with
            | None -> ()
            | Some unifier ->
                // TODO handle failures
                let argsByName =
                    prover.ExtractArgsByName
                        (expression,
                         unifier,
                         context,
                         normalizationMapping,
                         prover.VariablesByName,
                         prover.InputArgs,
                         prover.PassSubstitutionAs,
                         prover.PassContextAs)

                match prover.Handler with
                | Predicate handler ->
                    let truth = handler argsByName
                    if truth then
                        do! return'
                                { InferenceRule = prover
                                  Conclusion = unifier.ApplyTo(expression)
                                  Substitution = unifier
                                  Premises = Seq.empty }
                | MaybePredicate handler ->
                    match handler argsByName with
                    | Some true ->
                        do! return'
                                { InferenceRule = prover
                                  Conclusion = unifier.ApplyTo(expression)
                                  Substitution = unifier
                                  Premises = Seq.empty }
                    | _ -> ()
                | PremisedPredicate handler ->
                    let truth, premises = handler argsByName
                    if truth then
                        do! return'
                                { InferenceRule = prover
                                  Conclusion = unifier.ApplyTo(expression)
                                  Substitution = unifier
                                  Premises = premises }
                | Satisfier handler ->
                    let truth, substitution = handler argsByName
                    if truth then
                        do! return'
                                { InferenceRule = prover
                                  Conclusion = substitution.ApplyTo(expression)
                                  Substitution = substitution
                                  Premises = Seq.empty }
                | PremisedSatisfier handler ->
                    let truth, substitution, premises = handler argsByName
                    if truth then
                        do! return'
                                { InferenceRule = prover
                                  Conclusion = substitution.ApplyTo(expression)
                                  Substitution = substitution
                                  Premises = premises }
                | AsyncPredicate handler ->
                    let! truth = handler argsByName

                    if truth then
                        do! return'
                                { InferenceRule = prover
                                  Conclusion = unifier.ApplyTo(expression)
                                  Substitution = unifier
                                  Premises = Seq.empty }
                | AsyncMaybePredicate handler ->
                    match! handler argsByName with
                    | Some true ->
                        do! return'
                                { InferenceRule = prover
                                  Conclusion = unifier.ApplyTo(expression)
                                  Substitution = unifier
                                  Premises = Seq.empty }
                    | _ -> ()
                | AsyncPremisedPredicate handler ->
                    let! truth, premises = handler argsByName

                    if truth then
                        do! return'
                                { InferenceRule = prover
                                  Conclusion = unifier.ApplyTo(expression)
                                  Substitution = unifier
                                  Premises = premises }
                | AsyncSatisfier handler ->
                    let! truth, substitution = handler argsByName

                    if truth then
                        do! return'
                                { InferenceRule = prover
                                  Conclusion = substitution.ApplyTo(expression)
                                  Substitution = substitution
                                  Premises = Seq.empty }
                | AsyncPremisedSatisfier handler ->
                    let! truth, substitution, premises = handler argsByName

                    if truth then
                        do! return'
                                { InferenceRule = prover
                                  Conclusion = substitution.ApplyTo(expression)
                                  Substitution = substitution
                                  Premises = premises }
                | MultiSatisfier handler ->
                    for truth, substitution in handler argsByName do
                        if truth then
                            do! return'
                                    { InferenceRule = prover
                                      Conclusion = substitution.ApplyTo(expression)
                                      Substitution = substitution
                                      Premises = Seq.empty }
                | MultiPremisedSatisfier handler ->
                    for truth, substitution, premises in handler argsByName do
                        if truth then
                            do! return'
                                    { InferenceRule = prover
                                      Conclusion = substitution.ApplyTo(expression)
                                      Substitution = substitution
                                      Premises = premises }
                | AsyncSourcePredicate handler ->
                    do! handler argsByName (fun truth ->
                            async {
                                if truth then
                                    do! return'
                                            { InferenceRule = prover
                                              Conclusion = unifier.ApplyTo(expression)
                                              Substitution = unifier
                                              Premises = Seq.empty }
                            })
                | AsyncSourcePremisedPredicate handler ->
                    do! handler argsByName (fun (truth, premises) ->
                            async {
                                if truth then
                                    do! return'
                                            { InferenceRule = prover
                                              Conclusion = unifier.ApplyTo(expression)
                                              Substitution = unifier
                                              Premises = premises }
                            })
                | AsyncSourceSatisfier handler ->
                    do! handler argsByName (fun (truth, substitution) ->
                            async {
                                if truth then
                                    do! return'
                                            { InferenceRule = prover
                                              Conclusion = substitution.ApplyTo(expression)
                                              Substitution = substitution
                                              Premises = Seq.empty }
                            })
                | AsyncSourcePremisedSatisfier handler ->
                    do! handler argsByName (fun (truth, substitution, premises) ->
                            async {
                                if truth then
                                    do! return'
                                            { InferenceRule = prover
                                              Conclusion = substitution.ApplyTo(expression)
                                              Substitution = substitution
                                              Premises = premises }
                            })
        with
        | InvalidHandlerArgumentTypeException _ -> ()
    }
