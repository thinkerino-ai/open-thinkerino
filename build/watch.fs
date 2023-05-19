module Thinkerino.Build.Watch

open Fake.Core
open Fake.IO
open Fake.IO.Globbing.Operators
open Fake.DotNet

let runSubTarget subTarget =
    let res =
        sprintf "--project build %s" subTarget
        |> DotNet.exec (DotNet.Options.withWorkingDirectory ".") "run"

    if res.ExitCode <> 0 then
        failwithf "Dotnet tests failed: %A" (res.Results)

let init () =
    let rebuildTimeoutMinutes = 5
    let watcher = System.Diagnostics.Stopwatch.StartNew()

    Target.create "watch" (fun _ ->
        runSubTarget "retest"
        use thinkerinoWatcher =
            !! "thinkerino/**/*"
            -- "thinkerino/bin/**/*"
            -- "thinkerino/obj/**/*"
            |> ChangeWatcher.run (fun changes ->
                try
                    let elapsed = watcher.Elapsed
                    if elapsed.TotalMinutes > rebuildTimeoutMinutes then
                        runSubTarget "retest"
                        watcher.Restart()
                    else
                        runSubTarget "test.net"
                with
                | e -> printfn "thinkerinoWatcher Error: %s" (e.ToString()))

        use dotnetTestWatcher =
            !! "tests/**/*"
            -- "tests/bin/**/*"
            -- "tests/obj/**/*"
            |> ChangeWatcher.run (fun changes ->
                try
                    runSubTarget "test.net"
                with
                | e -> printfn "dotnetTestWatcher Error: %s" (e.ToString()))

        use thinkerinoJsWatcher =
            !! "thinkerino.js/**/*"
            -- "thinkerino.js/dist/**/*"
            -- "thinkerino.js/lib/**/*"
            |> ChangeWatcher.run (fun changes ->
                try
                    runSubTarget "test.js"
                with
                | e -> printfn "thinkerinoJsWatcher Error: %s" (e.ToString()))

        use thinkerinoPyWatcher =
            !! "thinkerino.py/**/*"
            -- "thinkerino.py/lib/**/*"
            -- "thinkerino.py/build/**/*"
            -- "thinkerino.py/dist/**/*"
            -- "thinkerino.py/thinkerino.egg-info/**/*"
            |> ChangeWatcher.run (fun changes ->
                try
                    // TODO debug why every now and then this runs again :P changes |> Seq.map (fun c -> c.FullPath) |> List.ofSeq |> printfn "changes: %O"
                    runSubTarget "test.py"
                with
                | e -> printfn "thinkerinoPyWatcher Error: %s" (e.ToString()))

        use thinkerinoCsWatcher =
            !! "thinkerino.cs/**/*"
            -- "thinkerino.cs/bin/**/*"
            -- "thinkerino.cs/obj/**/*"
            |> ChangeWatcher.run (fun changes ->
                try
                    runSubTarget "test.cs"
                with
                | e -> printfn "thinkerinoCsWatcher Error: %s" (e.ToString()))

        while true do
            System.Threading.Thread.Sleep(1000)

        thinkerinoWatcher.Dispose()
        thinkerinoCsWatcher.Dispose()
        thinkerinoJsWatcher.Dispose()
        thinkerinoPyWatcher.Dispose()
        dotnetTestWatcher.Dispose())
