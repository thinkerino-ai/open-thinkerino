module AITools.Utils.AsyncTools
open AITools.Utils.AsyncChannel

(* TODO:
    - limit the number of children spawned by the foreach*Parallel functions
    - make a computation expression for this (some sort of AsyncSeq, but fast :P)
*)

type ServiceMessage<'result> =
    | Start
    | Stop
    | Failure of exn
    | Result of 'result

/// A function used to rturn a value inside a data source
type ReturnFunction<'T> = 'T -> Async<unit>

/// A data source, runs asynchronously and can return data (even multiple times) by calling the passed ReturnFunction
type Source<'T> = ReturnFunction<'T> -> Async<unit>

/// Helper function to create a "broker-language" return function out of a channel
let toReturnFunc (channel: AsyncChannel<_>): ReturnFunction<_> = Result >> channel.AsyncAdd

/// Runs a source pushing its results on a channel, then pushes Stop to the channel
let runThenSignalStop (source: Source<_>) (channel: AsyncChannel<_>) =
    async {
        let! cancellationToken = Async.CancellationToken
        try
            do! source (channel |> toReturnFunc)
            Async.StartImmediate (channel.AsyncAdd Stop, cancellationToken)
        with
        | e -> Async.StartImmediate (channel.AsyncAdd (Failure e), cancellationToken)
    }

// TODO I don't think this is necessary :P
// /// Iterates over input values and executes an asynchronous body over each
// let foreach values body =
//     async {        
//         for value in values do
//             do! body value
    
//     }

/// Iterates over input values and for each result spawns a child which will run an asynchronous body over it.
/// Note: all children are spawned immediately.
let foreachParallel bufferSize values body =
    async {
        let! cancellationToken = Async.CancellationToken
        let channel = AsyncChannel(bufferSize)
        let mutable childrenCount = 0
        for value in values do
            childrenCount <- childrenCount + 1
            do! Async.StartChild
                    (async {
                        try
                            do! body value
                            Async.StartImmediate (channel.AsyncAdd Stop, cancellationToken)
                        with
                        | e -> Async.StartImmediate (channel.AsyncAdd (Failure e), cancellationToken)
                     })
                |> Async.Ignore
        while childrenCount > 0 do
            let! msg = channel.AsyncGet()

            match msg with
            | Stop -> childrenCount <- childrenCount - 1
            | Failure e -> raise e
            | _ -> failwith "Why did this receive anything but a Stop?"
    
    }

/// Reads input from a source and runs an asynchronous body over each value
let foreachResult bufferSize (source: Source<_>) body =
    async {
        let channel = AsyncChannel(bufferSize)
        let mutable childrenCount = 1
        do! Async.StartChild(runThenSignalStop source channel)
            |> Async.Ignore
        while childrenCount > 0 do
            let! msg = channel.AsyncGet()

            match msg with
            | Result value -> do! body value
            | Start -> childrenCount <- childrenCount + 1 // TODO does this ever happen? o.o
            | Stop -> childrenCount <- childrenCount - 1
            | Failure e -> raise e
    }

/// Reads input from a source and for each value starts a child which will run an asynchronous body over it.
/// Note: all children are spawned immediately.
let foreachResultParallel bufferSize (source: Source<_>) body =
    async {
        let! cancellationToken = Async.CancellationToken
        let channel = AsyncChannel(bufferSize)
        let mutable childrenCount = 1
        do! Async.StartChild(runThenSignalStop source channel)
            |> Async.Ignore
        while childrenCount > 0 do
            let! msg = channel.AsyncGet()

            match msg with
            | Start -> childrenCount <- childrenCount + 1 // TODO does this ever happen?
            | Stop -> childrenCount <- childrenCount - 1
            | Failure e -> raise e
            | Result value ->
                childrenCount <- childrenCount + 1
                do! Async.StartChild
                        (async {
                            try
                                do! body value
                                Async.StartImmediate (channel.AsyncAdd Stop, cancellationToken)
                            with
                            | e -> Async.StartImmediate (channel.AsyncAdd (Failure e), cancellationToken)
                         })
                    |> Async.Ignore
    }

/// Runs a source and yields each result synchronously (i.e. bridges the sync and async world)
let broker bufferSize source =
    seq {
        let cts = new System.Threading.CancellationTokenSource()
        let channel = AsyncChannel(bufferSize)
        Async.Start (runThenSignalStop source channel, cts.Token)
        let mutable childrenCount = 1
        try
            while childrenCount > 0 do
                match channel.Get() with
                | Stop -> childrenCount <- childrenCount - 1
                | Start -> failwith "Wait, why are you sending a Start to the broker?"
                | Result res -> yield res
                | Failure e -> raise e
        finally
            cts.Cancel()
            cts.Dispose()
    }
