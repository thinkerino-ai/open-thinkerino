module Thinkerino.Tests.Proofs.Provers
open AITools.Proofs.Language
open AITools.Proofs.Components.Provers
open Microsoft.FSharp.Core.LanguagePrimitives
open AITools.Proofs.Components.Base

#nowarn "25"

open AITools.Storage.Base
open AITools.Storage.Implementations.Dummy
open Expecto
open AITools.Proofs.KnowledgeBase
open AITools.Logic.Language
open AITools.Logic.Core
open AITools.Logic.Utils
open AITools.Proofs.Builtin.Provers

let storageImplementations: list<_ * (unit -> ExpressionStorage)> = [
    nameof DummyExpressionStorage, fun () -> upcast new DummyExpressionStorage()
    nameof DummyIndexedExpressionStorage, fun () -> upcast new DummyIndexedExpressionStorage()
]

let isKnownExpressionProofOf (kb: KnowledgeBase) expression (proof: Proof<_>) =
    Seq.isEmpty(proof.Premises) 
    && PhysicalEquality proof.InferenceRule kb.KnowledgeRetriever
    && proof.Substitution.ApplyTo(expression) = proof.Substitution.ApplyTo(proof.Conclusion)


let isEven (input: {| n: _ |}) = 
    input.n % 2 = 0

exception SomeException

let testWithImplementation (name, impl: unit -> ExpressionStorage) =
    let setupImplementation test () =
            use storage = impl()
            let kb = KnowledgeBase(storage)
            test kb

    testFixture setupImplementation [
        "we can retrieve known expressions", 
            fun testKb -> 
                let language = Language()
                let [IsA; dylan; cat] = makeManyNamed language ConstExpr ["IsA"; "dylan"; "cat"]
                let expr = makeExpr' (IsA, dylan, cat)
                testKb.AddExpression expr

                let proofs = testKb.Prove (expr, retrieveOnly=true) |> List.ofSeq

                Expect.hasLength proofs 1 "should have one proof"
                Expect.all 
                    proofs
                    (fun p -> p.Conclusion = expr)
                    "the conclusion should be the expression"
        // TODO test_retrieve_known_expression_transactional
        // TODO test_retrieve_known_expression_rollback
        "we can retrieve known open expressions", 
            fun testKb -> 
                let language = Language()
                let v = VarExprSource language
                let [IsA; dylan; cat; hugo] = makeManyNamed language ConstExpr ["IsA"; "dylan"; "cat"; "hugo"]

                let dylanIsACat = makeExpr' (IsA, dylan, cat)
                let hugoIsACat = makeExpr' (IsA, hugo, cat)
                testKb.AddExpressions <| seq {
                    dylanIsACat
                    hugoIsACat
                }

                let query = makeExpr' (IsA, v?x, cat)
                let proofs = testKb.Prove (query, retrieveOnly=true) |> List.ofSeq

                Expect.hasLength proofs 2 "should have two proofs"
                Expect.exists 
                    proofs
                    (fun p -> p.Conclusion = dylanIsACat)
                    "it should be known that dylan is a cat"
                Expect.exists 
                    proofs
                    (fun p -> p.Conclusion = hugoIsACat)
                    "it should be known that hugo is a cat"

        "open expressions are added only once",
            fun testKb ->
                let language = Language()
                let v = VarExprSource language

                let [Foo; a; b] = makeManyNamed language ConstExpr ["Foo"; "a"; "b"]
                
                testKb.AddExpressions <| seq {
                    makeExpr' (Foo, a, b)
                    makeExpr' (Foo, v?x, v?y)
                    makeExpr' (Foo, v?x, v?x)
                    // the following expression is not added, because it normalizes the same as the second expression
                    makeExpr' (Foo, v?w, v?z)
                }

                Expect.equal (testKb.Size) 3 "there should be three items"
        
        "expressions are normalized, so the same variables can be reused in axioms",
            fun testKb ->
                let language = Language()
                let v = VarExprSource language
                let [Foo; Bar; Baz; a; b] = makeManyNamed language ConstExpr ["Foo"; "Bar"; "Baz"; "a"; "b"]

                testKb.AddProver RestrictedModusPonens

                testKb.AddExpressions <| seq {
                    makeExpr' (Foo, a, b)
                    makeExpr' (Implies, (Foo, v?x, v?y), (Bar, v?x))
                    makeExpr' (Implies, (Bar, v?y), (Baz, v?y))
                }

                let query = makeExpr' (Baz, a)
                let proofs = testKb.Prove (query, retrieveOnly=false) |> List.ofSeq

                Expect.isNonEmpty proofs "there is at least a proof"
        
        "proofs can be repeated",
            fun testKb ->
                let language = Language()
                let v = VarExprSource language
                let [IsNatural; successor] = makeManyNamed language ConstExpr ["IsNatural"; "successor"]

                testKb.AddProver RestrictedModusPonens

                testKb.AddExpressions <| seq {
                    makeExpr' (IsNatural, Wrap(0))
                    makeExpr' (Implies, (IsNatural, v?x), (IsNatural, (successor, v?x)))
                }

                let query = makeExpr' (IsNatural, (successor, Wrap 0))
                let baselineProofs = testKb.Prove (query, retrieveOnly=false) |> List.ofSeq

                Expect.isNonEmpty baselineProofs "there is at least a proof the first time"
                
                let proofs = testKb.Prove (query, retrieveOnly=false) |> List.ofSeq

                Expect.isNonEmpty proofs "there is at least a proof the second time"

        "known expressions can be proven without additional provers",
            fun testKb ->
                let language = Language()

                let [IsA; dylan; cat] = makeManyNamed language ConstExpr ["IsA"; "dylan"; "cat"]

                testKb.AddExpression <|  makeExpr' (IsA, dylan, cat)

                let query = makeExpr' (IsA, dylan, cat)
                
                let proofs = testKb.Prove (query, retrieveOnly=false) |> List.ofSeq

                Expect.hasLength proofs 1 "there is at least a proof"
                Expect.all proofs (isKnownExpressionProofOf testKb query) "it is a known-fact proof of the query"
        
        "the knowledge base can prove an open expression",
            fun testKb ->
                let language = Language()
                let v = VariableSource language
                let [IsA; dylan; cat; hugo] = makeManyNamed language ConstExpr ["IsA"; "dylan"; "cat"; "hugo"]

                testKb.AddExpressions <|  seq {
                    makeExpr' (IsA, dylan, cat)
                    makeExpr' (IsA, hugo, cat)
                }

                let query = makeExpr' (IsA, Var(v?x), cat)
                
                let proofs = testKb.Prove (query, retrieveOnly=false) |> List.ofSeq

                Expect.hasLength proofs 2 "there are exactly 2 proofs"
                Expect.all proofs (isKnownExpressionProofOf testKb query) "it is a known-fact proof of the query"

                Expect.exists proofs (fun p -> p.Substitution.GetBoundObjectFor(v?x) = Some dylan) "we can prove that dylan is a cat"
                Expect.exists proofs (fun p -> p.Substitution.GetBoundObjectFor(v?x) = Some hugo) "we can prove that hugo is a cat"

        // TODO
        // def test_implication_shortcut():
        //     language = Language()
        //     v = VariableSource(language=language)
        //     IsA, cat, animal = constants('IsA, cat, animal', language=language)
        //     assert (IsA(v._x, cat) << Implies >> IsA(v._x, animal)) == (Implies(IsA(v._x, cat), IsA(v._x, animal)))

        "the knowledge base can perform simple deduction",
            fun testKb ->
                let language = Language()
                let v = VarExprSource language
                let [IsA; dylan; cat; animal] = makeManyNamed language ConstExpr ["IsA"; "dylan"; "cat"; "animal"]

                testKb.AddProver RestrictedModusPonens

                testKb.AddExpressions <|  seq {
                    makeExpr' (Implies, (IsA, v?x, cat), (IsA, v?x, animal))
                    makeExpr' (IsA, dylan, cat)
                }

                let query = makeExpr' (IsA, dylan, animal)
                
                let proofs = testKb.Prove (query, retrieveOnly=false) |> List.ofSeq

                Expect.hasLength proofs 1 "there is exactly 1 proof"

        // TODO do I want this? or should I delete it?
        // def test_retrieve_known_formula_does_not_use_deduction(test_knowledge_base):
        //     # this is the same as the basic retrieve case, but ensures deduction is not used
        //     language = Language()
        //     v = VariableSource(language=language)

        //     IsA, Purrs, dylan, cat = constants('IsA, Purrs, dylan, cat', language=language)
        //     test_knowledge_base.add_formulas(
        //         IsA(dylan, cat),
        //         Purrs(dylan)
        //     )

        //     # if it purrs like a cat, then it's a cat :P
        //     test_knowledge_base.add_formulas(
        //         Purrs(v.x) <<Implies>> IsA(v.x, cat)
        //     )

        //     # we can retrieve it because we already know it
        //     proofs = list(test_knowledge_base.prove(IsA(dylan, cat), retrieve_only=True))

        //     assert len(proofs) == 1

        "the knowledge base can perform a deduction chain",
            fun testKb ->
                let language = Language()
                let v = VarExprSource language
                let c = ConstExprSource language

                // TODO I like this new approach, I should apply it everywhere
                let IsA = c?IsA
                let dylan = c?dylan
                let cat = c?cat
                let animal = c?animal
                let mammal = c?mammal

                testKb.AddProver RestrictedModusPonens
                
                testKb.AddExpressions <|  seq {
                    Implies.E(IsA.E(v?x, cat), IsA.E(v?x, mammal))
                    makeExpr' (Implies, (IsA, v?x, mammal), (IsA, v?x, animal))
                    makeExpr' (IsA, dylan, cat)
                }

                let query = makeExpr' (IsA, dylan, animal)
                
                let proofs = testKb.Prove (query, retrieveOnly=false) |> List.ofSeq

                Expect.hasLength proofs 1 "there is exactly 1 proof"
                Expect.hasLength (proofs.Head.Premises) 2 "the proof has 2 premises"

        "custom provers can receive arbitrary values",
            fun testKb ->
                let language = Language()
                let v = VarExprSource language
                let c = ConstExprSource language

                let IsEven = c?IsEven
                let listenedExpression = IsEven.[v?n]

                let prover = 
                    makeProver 
                    <| HandlerDescriptor.MakeMapUnwrapped (listenedExpression, Predicate isEven, true, HandlerSafety.Safe)

                testKb.AddProver prover

                let proofs2 = testKb.Prove (IsEven.[2], false)
                Expect.hasLength proofs2 1 "there is exactly 1 proof that 2 is even"

                
                let proofs3 = testKb.Prove (IsEven.[3], false)

                // this means we can't prove it, not that we can prove it to be false
                Expect.hasLength proofs3 0 "there is no proof that 3 is even"

        "custom prover failure is propagated to the caller",
            fun testKb ->
                let language = Language()

                let v = VarExprSource language
                let c = ConstExprSource language

                let IsA = c?IsA
                let cat = c?cat
                let dylan = c?dylan

                let failingProver (input:{|cat: _|}) =
                    raise SomeException

                let listenedExpression = IsA.[v?cat, cat]

                let failing = 
                    makeProver 
                    <| HandlerDescriptor.MakeMapUnwrapped (listenedExpression, Predicate failingProver, true, HandlerSafety.Safe)

                testKb.AddProver failing

                testKb.AddExpression <|
                    IsA.[dylan, cat]

                Expect.throwsT<SomeException>
                    (fun () -> testKb.Prove(IsA.[dylan, cat], false) |> List.ofSeq |> ignore)
                    "the proving process throws the prover's exception"
                

    ]
    |> List.ofSeq
    |> testList name

[<Tests>]
let tests = 
    storageImplementations 
    |> List.map testWithImplementation
    |> testList "provers"