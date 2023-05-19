module Thinkerino.Build.CSharp
open Fake.Core
open Fake.Core.TargetOperators
open Fake.DotNet

let init () =
    // TODO remove this since I switched to paket
    // Target.create "install.cs" (fun _ -> DotNet.restore id "./thinkerino.cs")

    Target.create "clean.cs" (fun _ ->
        DotNet.exec (DotNet.Options.withWorkingDirectory "./thinkerino.cs") "clean" ""
        |> ignore)


    Target.create "build.cs" (fun _ -> DotNet.build (DotNet.Options.withWorkingDirectory "./thinkerino.cs") "")

    Target.create "test.cs" (fun _ -> DotNet.test id "./thinkerino.cs" |> ignore)

    // "install.cs" ==> "install" |> ignore
    "clean.cs" ?=> "build.cs" ?=> "test.cs" |> ignore
    "clean.cs" ==> "clean" |> ignore
    "build.cs" ==> "build" |> ignore
    "test.cs" ==> "test" |> ignore