// #r "nuget: Fake.Core.Target"
// #r "nuget: Fake.JavaScript.Npm"
// #r "paket:
// nuget Fake.Core.Target
// nuget Fake.JavaScript.Npm //"
// include Fake modules, see Fake modules section

open Fake.Core
open Fake.Core.TargetOperators


let initTargets () =
    Target.create "install" ignore // TODO include the paket restore (fun _ -> Paket.restore id)
    Target.create "clean" ignore
    Target.create "build" ignore
    Target.create "test" ignore
    Target.create "rebuild" ignore
    Target.create "retest" ignore
    Target.create "reretest" ignore
    Target.create "release" ignore

    Thinkerino.Build.BumpVersion.init ()
    Thinkerino.Build.JavaScript.init ()
    Thinkerino.Build.Python.init ()
    Thinkerino.Build.DotNet.init ()
    Thinkerino.Build.CSharp.init ()
    Thinkerino.Build.Watch.init ()

    "clean" ?=> "build" ?=> "test" |> ignore
    "build" ==> "rebuild" |> ignore
    "clean" ==> "rebuild" |> ignore
    "build" ==> "retest" |> ignore
    "rebuild" ==> "reretest" |> ignore
    "test" ==> "retest" |> ignore
    "build" ==> "release" |> ignore

// ==> "deploy"

// *** Start Build ***
[<EntryPoint>]
let main argv =
    argv
    |> Array.toList
    |> Context.FakeExecutionContext.Create false "build.fsx"
    |> Context.RuntimeContext.Fake
    |> Context.setExecutionContext

    initTargets ()
    Target.runOrDefaultWithArguments argv.[0]


    0 // return an integer exit code
