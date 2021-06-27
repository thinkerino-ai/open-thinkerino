module AITools.Utils.Logger

let logger =
    MailboxProcessor.Start(fun inbox ->
        async {
            while true do
                let! msg = inbox.Receive()
                printfn "%s" msg
        })

let debug msg = ()//logger.Post msg

let info msg = logger.Post msg