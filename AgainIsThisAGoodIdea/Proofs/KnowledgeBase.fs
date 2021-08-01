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
open AITools.Proofs.Components.Listeners




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

   
    member this.Ponder (expressions, ?previousSubstitution, ?bufferSize) =
        let previousSubstitution = defaultArg previousSubstitution Substitution.Empty
        let bufferSize = defaultArg bufferSize 1

        this.AsyncPonder (expressions, previousSubstitution, bufferSize) |> broker bufferSize
    
    member this.AsyncPonder (expressions, ?previousSubstitution, ?bufferSize) =
        let previousSubstitution = defaultArg previousSubstitution Substitution.Empty
        let bufferSize = defaultArg bufferSize 1
        
        fun return' -> foreachParallel bufferSize expressions <| fun expr -> async {
            let listeners = this.GetListenersFor(expr)
            do! foreachParallel bufferSize listeners <| fun listener ->
                ponder listener (TriggeringExpression expr, previousSubstitution, this) return'
        }

    member _.GetProversFor expression = seq{
        let key = makeKey(expression)
        yield! provers.Retrieve(key)
    }
    member _.GetListenersFor expression = seq{
        let key = makeKey(expression)
        yield! listeners.Retrieve(key)
    }