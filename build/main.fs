// #r "nuget: Fake.Core.Target"
// #r "nuget: Fake.JavaScript.Npm"
// #r "paket:
// nuget Fake.Core.Target
// nuget Fake.JavaScript.Npm //"
// include Fake modules, see Fake modules section

open Fake.Core
open Fake.Core.TargetOperators

open Fake.Tools

let transform =
    """<?xml version="1.0" encoding="utf-8"?>
<Project xmlns:xdt="http://schemas.microsoft.com/XML-Document-Transform">
  <PropertyGroup>
    <Version xdt:Transform="Replace" xdt:Locator="Match(Version)">1.33.4</Version>
  </PropertyGroup>
</Project>
"""

//type PackageJSON = FSharp.Data.JsonProvider<"""{"version": "0.0.1"}""">
//type PackageJSON = FSharp.Data.JsonProvider<"../thinkerino.js/package.json">

let initTargets () =
    Target.create "install" ignore // TODO include the paket restore (fun _ -> Paket.restore id)
    Target.create "clean" ignore
    Target.create "build" ignore
    Target.create "test" ignore
    Target.create "rebuild" ignore
    Target.create "retest" ignore
    Target.create "reretest" ignore

    Target.create "release" (fun _ ->
        let semVer =
            (GitVersion.generateProperties (fun cfg ->
                { cfg with
                    ToolPath = "dotnet-gitversion"
                    ToolType = Fake.DotNet.ToolType.CreateLocalTool() }))
                .FullSemVer

        Xml.pokeInnerText "thinkerino/thinkerino.fsproj" "/Project/PropertyGroup/Version" semVer
        Xml.pokeInnerText "thinkerino.cs/thinkerino.cs.csproj" "/Project/PropertyGroup/Version" semVer



        let rawpjson =
            Fake.IO.File.readAsString "thinkerino.js/package.json"

        Fake.JavaScript.Npm.run (sprintf "set-version %s" semVer) (fun o ->
            { o with WorkingDirectory = "./thinkerino.js" })

        Fake.IO.File.replaceContent "thinkerino.py/VERSION" semVer)

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
