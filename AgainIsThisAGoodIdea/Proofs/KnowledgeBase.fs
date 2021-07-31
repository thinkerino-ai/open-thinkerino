module AITools.Proofs.KnowledgeBase
open AITools.Proofs.Components.Provers
open AITools.Storage.Base
open AITools.Storage.Implementations.Dummy
open AITools.Logic.Language
open AITools.Logic.Core
open AITools.Logic.Utils
open AITools.Proofs.Components.Base
open AITools.Utils.AsyncTools
open AITools.Storage.Index
open AITools.Logic.Unification
open System




type KnowledgeBase(storage: ExpressionStorage) = 
    let language = Language()
    
    let makeVarWithIntName (lang, intName: int option) = Variable (lang, Option.map string intName)
    let variableSource = Source<_,_> <| makeNamed language makeVarWithIntName

    let provers = DummyAbstruseIndex()
    let listeners = DummyAbstruseIndex()

    
    let retrieveKnowledge (input:{|expression: _; substitution:_; kb: KnowledgeBase|}) return' = async{
        for res in (input.kb.Retrieve input.expression  input.substitution) do 
            do! return' res
    }

    let knowledgeRetriever = 
        makeProver
        <| HandlerDescriptor.MakeRaw(
            make language VarExpr,
            AsyncSourceSatisfier retrieveKnowledge,
            Some false,
            HandlerSafety.Safe
        )

    // TODO
    // def supports_transactions(self) -> bool:
    //     return self._storage.supports_transactions()
    // @contextmanager
    // def transaction(self):
    //     with self._storage.transaction():
    //         yield
    // def commit(self):
    //     self._storage.commit()
    // def rollback(self):
    //     self._storage.rollback()

    /// Retrieves all expressions from the Storage which are unifiable with the given one.
    /// No proof is searched, so either a formula is **IN** the storate or nothing will be returned
    member private _.Retrieve expression previouSubstitution = seq {
        (* note: this is not async (while the Python version was), because right now there is neither need nor support for it in the Storage :P
            it was not necessary in Python either, but... you know... :P I'm a dummy dum dum *)
        for expr, _ in storage.SearchUnifiable expression do
            let normalizedExpr, _ = normalizeVariables variableSource expr
            let subst = Substitution.Unify(normalizedExpr, expression, previouSubstitution)

            match subst with
            | Some s -> yield (true, s)
            | None -> ()
    }

    /// Adds all of the given formulas to the currently known formulas, after normalization
    member _.AddFormulas =       
        Seq.map (normalizeVariables variableSource >> fst) 
        >> storage.Add

    member _.AddProver (prover: Prover<_>) =
        let key = makeKey prover.ListenedExpression
        provers.Add(key, prover)
    
    // TODO
    // member _.AddListener (listener: Listener<_>) =
    //     let key = makeKey listener.ListenedExpression
    //     Listeners.Add(key, listener)

    member _.Size with get() = storage.Size


    member this.Prove (expression, retrieveOnly, ?previousSubstitution, ?bufferSize) =
        // TODO 
        // if asynctools.is_inside_task():
        //     raise RuntimeError(f"{KnowledgeBase.__name__}.{KnowledgeBase.prove.__name__} cannot be used "
        //                        f"inside tasks")
        let previousSubstitution = defaultArg previousSubstitution Substitution.Empty
        let bufferSize = defaultArg bufferSize 1

        // TODO buffer size
        this.AsyncProve (expression, retrieveOnly, previousSubstitution, bufferSize) |> broker bufferSize

        
    member this.AsyncProve (expression, retrieveOnly, ?previousSubstitution, ?bufferSize): Source<_> = 
        let previousSubstitution = defaultArg previousSubstitution Substitution.Empty
        let bufferSize = defaultArg bufferSize 1
        
        // TODO
        // if not asynctools.is_inside_task():
        //     raise RuntimeError(f"{KnowledgeBase.__name__}.{KnowledgeBase.async_prove.__name__} cannot be used "
        //                        f"outside tasks")

        let provers: list<Prover<_>> = 
            if retrieveOnly then
                [knowledgeRetriever]
            else
                // TODO I should probably apply the substitution to the expression, otherwise I'd consider more provers than necessary
                knowledgeRetriever :: (List.ofSeq <| this.GetProversFor(expression))

        // TODO buffer size
        fun return' -> foreachParallel bufferSize provers <| fun prover -> prove prover (expression, previousSubstitution, this) return'

    // TODO
    // def ponder(self, *formulas: Iterable[LogicObject], ponder_mode: PonderMode):
    //     proving_process = self.__make_proving_process(formulas, ponder_mode)

    //     # TODO make buffer_size configurable
    //     for proof in self._scheduler.schedule_generator(
    //             process_with_loopback(input_sequence=proving_process, processor=self.__ponder_single_proof),
    //             buffer_size=1
    //     ):
    //         yield proof

    // def __make_proving_process(self, formulas, ponder_mode):
    //     if ponder_mode == PonderMode.HYPOTHETICALLY:
    //         raise NotImplementedError("This case requires hypotheses to be implemented :P")
    //     elif ponder_mode == PonderMode.KNOWN:
    //         # TODO make buffer_size configurable
    //         proving_process = asynctools.multiplex(
    //             *(self.async_prove(f, retrieve_only=True) for f in formulas),
    //             buffer_size=1
    //         )
    //     elif ponder_mode == PonderMode.PROVE:
    //         # TODO make buffer_size configurable
    //         proving_process = asynctools.multiplex(
    //             *(self.async_prove(f, retrieve_only=False) for f in formulas),
    //             buffer_size=1
    //         )
    //     else:
    //         raise NotImplementedError(f"Unknown ponder mode: {ponder_mode}")
    //     return proving_process

    // async def __ponder_single_proof(self, proof: Proof, *, queue: asyncio.Queue, poison_pill):
    //     pondering_sources = []
    //     for listener in self.get_listeners_for(proof.conclusion):
    //         trigger_premise = Proof(
    //             inference_rule=TriggeringFormula(),
    //             conclusion=proof.substitution.apply_to(proof.conclusion),
    //             substitution=proof.substitution,
    //             premises=(proof,)
    //         )
    //         pondering_sources.append(listener.ponder(trigger_premise, knowledge_base=self))

    //     # TODO make buffer_size configurable
    //     pondering_process = asynctools.multiplex(
    //         *pondering_sources,
    //         buffer_size=1
    //     )

    //     await asynctools.push_each_to_queue(pondering_process, queue=queue, poison_pill=poison_pill)

    // def get_listeners_for(self, formula):
    //     key = make_key(formula)
    //     yield from self._listener_storage.retrieve(key)


    member _.GetProversFor expression = seq{
        let key = makeKey(expression)
        yield! provers.Retrieve(key)
    }