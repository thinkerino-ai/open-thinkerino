module Thinkerino.Proofs.Builtin.Provers

open Thinkerino.Logic.Language
open Thinkerino.Logic.Utils
open Thinkerino.Logic.Core
open Thinkerino.Proofs.Components.Base
open Thinkerino.Proofs.Components.Provers
open Thinkerino.Proofs.KnowledgeBase
open Thinkerino.Proofs.Language
open System.Collections.Immutable
open Thinkerino.Utils.AsyncTools

let private language = Language()

// TODO this can't be a constant here, but still we need it somewhere
let bufferSize = 1

let private restrictedModusPonens (input:{|expression: _; substitution:_; kb: KnowledgeBase|}) return' = async{
    let v = VariableSource language
    
    match input.expression with
    | Expr children when children.Length > 0 && children.[0] = Implies -> ()
    | _ ->
        let rulePattern = [|Implies; Var(v?premise); input.expression|] |> ImmutableArray.CreateRange |> Expr
        let ruleProofs = input.kb.AsyncProve (rulePattern, false, input.substitution, bufferSize)
        do! foreachResultParallel bufferSize ruleProofs <| fun ruleProof -> async{
            match ruleProof.Substitution.GetBoundObjectFor(v?premise) with
            | Some premise -> 
                let premiseProofs = input.kb.AsyncProve(premise, false, ruleProof.Substitution, bufferSize)
                do! foreachResultParallel bufferSize premiseProofs <| fun premiseProof ->
                    return' (true, premiseProof.Substitution, seq{ruleProof; premiseProof})
            | None -> ()
        }
}


let RestrictedModusPonens: Prover<KnowledgeBase> = 
    makeProver <| HandlerDescriptor.MakeRaw(
        make language VarExpr,
        AsyncSourcePremisedSatisfier restrictedModusPonens,
        HandlerPurity.Impure,
        HandlerSafety.Safe,
        PassSubstitutionAs "substitution",
        PassContextAs "kb"
    )


// async def closed_world_assumption(formula: LogicObject, substitution: Substitution, kb: KnowledgeBase):
//     language = Language()
//     v = VariableSource(language=language)
//     match = Substitution.unify(formula, Not(v.P))
//     if match is not None:
//         try:
//             await kb.async_prove(match.get_bound_object_for(v.P)).__anext__()
//         except StopAsyncIteration:
//             return TruthSubstitution(True, substitution)


// ClosedWorldAssumption = Prover(
//     listened_formula=Variable(language=language), handler=closed_world_assumption, argument_mode=HandlerArgumentMode.RAW,
//     pass_substitution_as=..., pass_knowledge_base_as='kb', pure=True, safety=HandlerSafety.SAFE
// )