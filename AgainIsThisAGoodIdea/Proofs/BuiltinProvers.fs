module AITools.Proofs.Builtin.Provers

open AITools.Logic.Language
open AITools.Logic.Utils
open AITools.Logic.Core
open AITools.Proofs.Components.Base
open AITools.Proofs.Components.Provers
open AITools.Proofs.KnowledgeBase
open AITools.Proofs.Language
open System.Collections.Immutable
open AITools.Utils.AsyncTools

let private language = Language()

// TODO this can't be a constant here, but still we need it somewhere
let bufferSize = 1

let private restrictedModusPonens (input:{|expression: _; substitution:_; kb: KnowledgeBase|}) return' = async{
    let v = VariableSource language
    
    match input.expression with
    | Expr children when children.Length > 0 && children.[0] = Implies -> ()
    | _ ->
        let rulePattern = [|Implies; Var(v.["premise"]); input.expression|] |> ImmutableArray.CreateRange |> Expr
        let ruleProofs = input.kb.AsyncProve (rulePattern, false, input.substitution, bufferSize)
        do! foreachResultParallel bufferSize ruleProofs <| fun ruleProof -> async{
            match ruleProof.Substitution.GetBoundObjectFor(v.["premise"]) with
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
        Some false,
        HandlerSafety.Safe,
        passContextAs="kb"
    )