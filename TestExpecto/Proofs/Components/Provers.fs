module Thinkerino.Tests.Proofs.Components.Provers

#nowarn "25"

open AITools.Proofs.Language
open AITools.Proofs.Components.Provers
open Microsoft.FSharp.Core.LanguagePrimitives
open AITools.Proofs.Components.Base
open AITools.Utils.AsyncTools
open Thinkerino.Tests.Utils

open AITools.Proofs.KnowledgeBase
open Expecto
open AITools.Logic.Language
open AITools.Logic.Core
open AITools.Logic.Utils
open AITools.Proofs.Builtin.Provers

let isKnownExpressionProofOf (kb: KnowledgeBase) expression (proof: Proof<_>) =
    Seq.isEmpty(proof.Premises) 
    && PhysicalEquality proof.InferenceRule kb.KnowledgeRetriever
    && proof.Substitution.ApplyTo(expression) = proof.Substitution.ApplyTo(proof.Conclusion)


let isEven (input: {| n: _ |}) = 
    input.n % 2 = 0

let isPrime (input: {|n: _|}) =
    if List.contains input.n [2; 3; 5; 7] then Some true
    else if List.contains input.n [4; 6; 8] then Some false
    else None

exception SomeException

let proverTestMakers (setup: (KnowledgeBase -> unit) -> unit) = [
        test "we can retrieve known expressions" { 
            setup <| fun testKb -> 
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
            }
            // TODO test_retrieve_known_expression_transactional
            // TODO test_retrieve_known_expression_rollback
        test "we can retrieve known open expressions" {
            setup <| fun testKb -> 
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

            }
        test "open expressions are added only once" {
            setup <| fun testKb -> 

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
            }
        test "expressions are normalized, so the same variables can be reused in axioms" {
            setup <| fun testKb -> 
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
            
            }
        test "proofs can be repeated" {
            setup <| fun testKb -> 
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
            }
        test "known expressions can be proven without additional provers" {
            setup <| fun testKb -> 
                let language = Language()

                let [IsA; dylan; cat] = makeManyNamed language ConstExpr ["IsA"; "dylan"; "cat"]

                testKb.AddExpression <| IsA.[dylan, cat]

                let query = makeExpr' (IsA, dylan, cat)
                
                let proofs = testKb.Prove (query, retrieveOnly=false) |> List.ofSeq

                Expect.hasLength proofs 1 "there is at least a proof"
                Expect.all proofs (isKnownExpressionProofOf testKb query) "it is a known-fact proof of the query"
            }
        test "the knowledge base can prove an open expression" {
            setup <| fun testKb -> 
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

            }
        test "the knowledge base can perform simple deduction" {
            setup <| fun testKb -> 
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

            }
        test "the knowledge base can perform a deduction chain" {
            setup <| fun testKb -> 
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
            }
        test "custom provers can receive arbitrary values" {
            setup <| fun testKb -> 
                let language = Language()
                let v = VarExprSource language
                let c = ConstExprSource language

                let IsEven = c?IsEven
                let listenedExpression = IsEven.[v?n]

                let prover = 
                    makeProver 
                    <| HandlerDescriptor.MakeMapUnwrappedRequired (listenedExpression, Predicate isEven, HandlerPurity.Pure, HandlerSafety.Safe, NoSubstitution, NoContext)

                testKb.AddProver prover

                let proofs2 = testKb.Prove (IsEven.[2], false)
                Expect.hasLength proofs2 1 "there is exactly 1 proof that 2 is even"

                
                let proofs3 = testKb.Prove (IsEven.[3], false)

                // this means we can't prove it, not that we can prove it to be false
                Expect.hasLength proofs3 0 "there is no proof that 3 is even"
            }
        test "custom prover failure is propagated to the caller" {
            setup <| fun testKb -> 
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
                    <| HandlerDescriptor.MakeMapUnwrapped (listenedExpression, Predicate failingProver, HandlerPurity.Pure, HandlerSafety.Safe, NoSubstitution, NoContext)

                testKb.AddProver failing

                testKb.AddExpression <|
                    IsA.[dylan, cat]

                Expect.throwsT<SomeException>
                    (fun () -> testKb.Prove(IsA.[dylan, cat], false) |> List.ofSeq |> ignore)
                    "the proving process throws the prover's exception"
            }
        test "custom provers can be chained" {
            setup <| fun testKb -> 
                let language = Language()
                let v = VarExprSource language
                let c = ConstExprSource language

                let IsEven = c?IsEven
                let IsMultipleOf4 = c?IsMultipleOf4

                let isMultipleOf4 (input: {|m: _; kb: KnowledgeBase|}) return' =
                   foreachResult 1 (input.kb.AsyncProve(IsEven.[input.m/2], false)) return'
                
                let evenProver = 
                    makeProver 
                    <| HandlerDescriptor.MakeMapUnwrappedRequired (IsEven.[v?n], Predicate isEven, HandlerPurity.Pure, HandlerSafety.Safe, NoSubstitution, NoContext)
                let multipleOf4Prover = 
                    makeProver 
                    <| HandlerDescriptor.MakeMapUnwrappedRequired (IsMultipleOf4.[v?n], Predicate isEven, HandlerPurity.Pure, HandlerSafety.Safe, NoSubstitution, PassContextAs "kb")

                testKb.AddProver evenProver
                testKb.AddProver multipleOf4Prover

                let proofs = testKb.Prove (IsMultipleOf4.[20], false) |> List.ofSeq
                Expect.hasLength proofs 1 "there is exactly 1 proof that 20 is multiple of 4"
                
            // TODO wait... what? what is this test? the name makes no sense, but the original was test_custom_prover_in_open_formula
            }
        test "custom provers work with open expressions" {
            setup <| fun testKb -> 
                let language = Language()
                let v = VarExprSource language
                let c = ConstExprSource language

                let IsEven = c?IsEven
                let IsNice = c?IsNice
                
                let listenedExpression = IsEven.[v?n]

                let prover = 
                    makeProver 
                    <| HandlerDescriptor.MakeMapUnwrappedRequired (listenedExpression, Predicate isEven, HandlerPurity.Pure, HandlerSafety.Safe, NoSubstitution, NoContext)

                testKb.AddProver prover
                testKb.AddProver RestrictedModusPonens

                // I don't actually like even numbers, unless they are powers of 2
                testKb.AddExpression <| Implies.[IsEven.[v?x], IsNice.[v?x]]

                let proofs = testKb.Prove (IsNice.[32], false)
                Expect.hasLength proofs 1 "there is exactly 1 proof that 32 is nice"
            }
        test "if a prover returns no response, no proof is found" {
            setup <| fun testKb -> 
                let language = Language()
                let v = VarExprSource language
                let c = ConstExprSource language

                let IsPrime = c?IsPrime
                let listenedExpression = IsPrime.[v?n]

                let prover = 
                    makeProver 
                    <| HandlerDescriptor.MakeMapUnwrappedRequired (listenedExpression, MaybePredicate isPrime, HandlerPurity.Pure, HandlerSafety.Safe, NoSubstitution, NoContext)

                testKb.AddProver prover

                let proofs2 = testKb.Prove (IsPrime.[2], false)
                Expect.hasLength proofs2 1 "there is exactly 1 proof that 2 is prime"

                let proofs8 = testKb.Prove (IsPrime.[8], false)
                Expect.hasLength proofs8 0 "there is no proof that 8 is prime"
                
                let proofs10 = testKb.Prove (IsPrime.[10], false)
                Expect.hasLength proofs10 0 "there is no proof that 10 is prime"
            }
        test "if a multiple custom provers can prove something, multiple proofs are found" {
            setup <| fun testKb -> 
                let language = Language()
                let v = VarExprSource language
                let c = ConstExprSource language

                let primeProver_012345 (input: {|n: _|}) =
                    if List.contains input.n [2; 3; 5] then Some true
                    else if List.contains input.n [0; 1; 4] then Some false
                    else None
                
                let primeProver_456789 (input: {|n: _|}) =
                    if List.contains input.n [5; 7] then Some true
                    else if List.contains input.n [4; 6; 8; 9] then Some false
                    else None

                let IsPrime = c?IsPrime
                let listenedExpression = IsPrime.[v?n]

                let prover1 = 
                    makeProver 
                    <| HandlerDescriptor.MakeMapUnwrappedRequired (listenedExpression, MaybePredicate primeProver_012345, HandlerPurity.Pure, HandlerSafety.Safe, NoSubstitution, NoContext)
                let prover2 = 
                    makeProver 
                    <| HandlerDescriptor.MakeMapUnwrappedRequired (listenedExpression, MaybePredicate primeProver_456789, HandlerPurity.Pure, HandlerSafety.Safe, NoSubstitution, NoContext)

                testKb.AddProver prover1
                testKb.AddProver prover2
                
                Expect.hasLength 
                    (testKb.Prove (IsPrime.[2], false))
                    1 
                    "there is exactly 1 proof that 2 is prime"

                Expect.hasLength 
                    (testKb.Prove (IsPrime.[7], false))
                    1 
                    "there is exactly 1 proof that 7 is prime"

                Expect.hasLength 
                    (testKb.Prove (IsPrime.[5], false))
                    2
                    "there are exactly 2 proofs that 5 is prime"

                Expect.isEmpty 
                    (testKb.Prove (IsPrime.[11], false))
                    "there is no proof that 11 is prime"
            }

            /////////////////////////////////////////////////////////

        test "custom Raw provers are not called when argument types are incompatible with the handler" {
            setup <| fun testKb -> 
                let language = Language()
                let v = VarExprSource language
                let c = ConstExprSource language

                let IsEven, foo = c?IsEven, c?foo
                let listenedExpression = IsEven.[v?n]

                let handler (input: {|expression: int; substitution: int|}) = true

                let prover = 
                    makeProver 
                    <| HandlerDescriptor.MakeRaw (listenedExpression, Predicate handler, HandlerPurity.Pure, HandlerSafety.Safe, PassSubstitutionAs "substitution", NoContext)

                testKb.AddProver prover

                let proofs = testKb.Prove (IsEven.[foo], false)
                Expect.isEmpty proofs "no proof is found, but we still get here (no exception)"
            }
        test "custom Map provers are not called when argument types are incompatible with the handler" {
            setup <| fun testKb -> 
                let language = Language()
                let v = VarExprSource language
                let c = ConstExprSource language

                let IsEven, foo = c?IsEven, c?foo
                let listenedExpression = IsEven.[v?n]

                let prover = 
                    makeProver 
                    <| HandlerDescriptor.MakeMap (listenedExpression, Predicate isEven, HandlerPurity.Pure, HandlerSafety.Safe, NoSubstitution, NoContext)

                testKb.AddProver prover

                let proofs = testKb.Prove (IsEven.[foo], false)
                Expect.isEmpty proofs "no proof is found, but we still get here (no exception)"
            }
        test "custom MapUnwrapped provers are not called when argument types are incompatible with the handler" {
            setup <| fun testKb -> 
                let language = Language()
                let v = VarExprSource language
                let c = ConstExprSource language

                let IsEven, foo = c?IsEven, c?foo
                let listenedExpression = IsEven.[v?n]

                let prover = 
                    makeProver 
                    <| HandlerDescriptor.MakeMapUnwrapped (listenedExpression, Predicate isEven, HandlerPurity.Pure, HandlerSafety.Safe, NoSubstitution, NoContext)

                testKb.AddProver prover

                let proofs = testKb.Prove (IsEven.[foo], false)
                Expect.isEmpty proofs "no proof is found, but we still get here (no exception)"
            }
        test "custom MapUnwrappedRequired provers are not called when argument types are incompatible with the handler" {
            setup <| fun testKb -> 
                let language = Language()
                let v = VarExprSource language
                let c = ConstExprSource language

                let IsEven, foo = c?IsEven, c?foo
                let listenedExpression = IsEven.[v?n]

                let prover = 
                    makeProver 
                    <| HandlerDescriptor.MakeMapUnwrappedRequired (listenedExpression, Predicate isEven, HandlerPurity.Pure, HandlerSafety.Safe, NoSubstitution, NoContext)

                testKb.AddProver prover

                let proofs = testKb.Prove (IsEven.[foo], false)
                Expect.isEmpty proofs "no proof is found, but we still get here (no exception)"
            }
        test "custom MapUnwrappedNoVariables provers are not called when argument types are incompatible with the handler" {
            setup <| fun testKb -> 
                let language = Language()
                let v = VarExprSource language
                let c = ConstExprSource language

                let IsEven, foo = c?IsEven, c?foo
                let listenedExpression = IsEven.[v?n]

                let prover = 
                    makeProver 
                    <| HandlerDescriptor.MakeMapUnwrappedNoVariables (listenedExpression, Predicate isEven, HandlerPurity.Pure, HandlerSafety.Safe, NoSubstitution, NoContext)

                testKb.AddProver prover

                let proofs = testKb.Prove (IsEven.[foo], false)
                Expect.isEmpty proofs "no proof is found, but we still get here (no exception)"
            }
        test "custom MapUnwrappedNoVariables provers are not called when a variable is passed as input" {
            setup <| fun testKb -> 
                let language = Language()
                let v = VarExprSource language
                let c = ConstExprSource language

                let IsEven, foo = c?IsEven, c?foo
                let listenedExpression = IsEven.[v?n]

                let prover = 
                    makeProver 
                    <| HandlerDescriptor.MakeMapUnwrappedNoVariables (listenedExpression, Predicate isEven, HandlerPurity.Pure, HandlerSafety.Safe, NoSubstitution, NoContext)

                testKb.AddProver prover
                
                let proofs = testKb.Prove (IsEven.[v?x], false)
                Expect.isEmpty proofs "no proof is found, but we still get here (no exception)"
            }
        test "custom MapNoVariables provers are not called when argument types are incompatible with the handler" {
            setup <| fun testKb -> 
                let language = Language()
                let v = VarExprSource language
                let c = ConstExprSource language

                let IsEven, foo = c?IsEven, c?foo
                let listenedExpression = IsEven.[v?n]

                let prover = 
                    makeProver 
                    <| HandlerDescriptor.MakeMapNoVariables (listenedExpression, Predicate isEven, HandlerPurity.Pure, HandlerSafety.Safe, NoSubstitution, NoContext)

                testKb.AddProver prover

                let proofs = testKb.Prove (IsEven.[foo], false)
                Expect.isEmpty proofs "no proof is found, but we still get here (no exception)"
            }
        test "custom MapNoVariables provers are not called when a variable is passed as input" {
            setup <| fun testKb -> 
                let language = Language()
                let v = VarExprSource language
                let c = ConstExprSource language

                let IsEven, foo = c?IsEven, c?foo
                let listenedExpression = IsEven.[v?n]

                let prover = 
                    makeProver 
                    <| HandlerDescriptor.MakeMapNoVariables (listenedExpression, Predicate isEven, HandlerPurity.Pure, HandlerSafety.Safe, NoSubstitution, NoContext)

                testKb.AddProver prover

                let proofs = testKb.Prove (IsEven.[v?x], false)
                Expect.isEmpty proofs "no proof is found, but we still get here (no exception)"
            }
        
        //////////////////////////////////////////////////////////
        // TODO
        // def test_closed_world_assumption(test_knowledge_base):
        //     language = Language()
        //     v = VariableSource(language=language)
        //     IsPrime = MagicPredicate(language=language)
        //     prover = Prover(
        //         listened_formula=IsPrime(v.n), handler=is_prime, argument_mode=HandlerArgumentMode.MAP_UNWRAPPED_REQUIRED,
        //         pass_substitution_as=..., pure=True, safety=HandlerSafety.SAFE
        //     )
        //     test_knowledge_base.add_prover(prover)
        //     test_knowledge_base.add_prover(RestrictedModusPonens)
        //     assert not any(test_knowledge_base.prove(Not(IsPrime(4))))
        //     test_knowledge_base.add_prover(ClosedWorldAssumption)
        //     assert any(test_knowledge_base.prove(Not(IsPrime(4))))
        // @pytest.mark.xfail(reason="me == lazy")
        // def test_result_order():
        //     # TODO this test should use "complex" chains and show that results are generated breadth-first-ish
        //     raise NotImplementedError()
        // @pytest.mark.xfail(reason="me == lazy")
        // def test_handler_result_types():
        //     # TODO this should actually be several tests that check every possible type returned by a handler (sync and async)
        //     raise NotImplementedError()
        // @pytest.mark.xfail(reason="Come on, we can bring coverage up :P")
        // def test_many_more_cases():
        //     raise NotImplementedError("Implement all possible input modes")
    
    ]

[<Tests>]
let proverTests = 
    proverTestMakers
    |> runWithKb
    |> testList "provers"