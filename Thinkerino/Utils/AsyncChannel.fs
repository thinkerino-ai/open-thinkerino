module Thinkerino.Utils.AsyncChannel 

type SpinAsyncEvent<'value>() =
    let mutable result: 'value option = None

    member _.AsyncAwaitable =
        async {
            while result.IsNone do
                do! Async.Sleep 0

            return result.Value
        }

    member _.Trigger value = result <- Some value

type AsyncChannel<'value>(bufferSize) =
    let locker = obj ()

    let resultQueue =
        System.Collections.Generic.Queue<'value>()

    let pullQueue =
        System.Collections.Generic.Queue<SpinAsyncEvent<_>>()

    let pushQueue = System.Collections.Generic.Queue()

    let enqueue value =
        let enqueuer =
            lock locker (fun () ->
                // se la resultQueue è piena, accodo un pusher con il valore e restituisco un async che attende quel push
                if resultQueue.Count = bufferSize then
                    let pusher = SpinAsyncEvent()
                    pushQueue.Enqueue(pusher, value)
                    async {
                        do! pusher.AsyncAwaitable
                    }
                // se la resultQueue è vuota e la pullQueue ha un puller, triggero il puller e restituisco async { return () }
                elif resultQueue.Count = 0 && pullQueue.Count > 0 then
                    let puller = pullQueue.Dequeue()
                    puller.Trigger value
                    async { return () }
                // altrimenti aggiungo il risultato alla resultQueue e restituisco async { return () }
                else
                    resultQueue.Enqueue value
                    async { return () })
        enqueuer

    let dequeue () =
        let dequeuer =
            lock locker (fun () ->

                // se la resultQueue è vuota, accodo un puller e restituisco un async che attende quel puller
                if resultQueue.Count = 0 then
                    let puller = SpinAsyncEvent()
                    pullQueue.Enqueue puller
                    async {
                        let! res = puller.AsyncAwaitable
                        return res

                    }
                // se la resultQueue è piena e la pushQueue ha un pusher, scodo da entrambe, triggero il pusher con (), accodo il valore del pusher e restituisco async { return res }
                elif resultQueue.Count = bufferSize
                     && pushQueue.Count > 0 then
                    let res = resultQueue.Dequeue()
                    let pusher, incoming = pushQueue.Dequeue()
                    resultQueue.Enqueue incoming
                    pusher.Trigger()

                    async { return res }
                // altrimenti scodo dalla resultQueue e restituisco async { return res }
                else
                    let res = resultQueue.Dequeue()
                    async { return res })
        dequeuer

    member _.Get() = Async.RunSynchronously <| dequeue ()

    member _.Add value = Async.RunSynchronously <| enqueue value

    member _.AsyncGet() = dequeue ()
    member _.AsyncAdd value = enqueue value

