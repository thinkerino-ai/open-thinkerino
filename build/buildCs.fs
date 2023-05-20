module Thinkerino.Build.CSharp
open Fake.Core
open Fake.Core.TargetOperators
open Fake.DotNet

open Thinkerino.Build.Utils

let applyVersion = Xml.pokeInnerText "thinkerino.cs/thinkerino.cs.csproj" "/Project/PropertyGroup/Version"

let init () =
    // TODO remove this since I switched to paket
    // Target.create "install.cs" (fun _ -> DotNet.restore id "./thinkerino.cs")

    Target.create "clean.cs" (fun _ ->
        DotNet.exec (DotNet.Options.withWorkingDirectory "./thinkerino.cs") "clean" ""
        |> ignore)


    Target.create "build.cs" (fun _ -> DotNet.build (DotNet.Options.withWorkingDirectory "./thinkerino.cs") "")

    Target.create "test.cs" (fun _ -> DotNet.test id "./thinkerino.cs" |> ignore)

    Target.create "release.cs" (fun _ ->
        let semVer = getSemVer ()

        applyVersion semVer
        let destDir = sprintf "%s/dist/dotnet" (System.IO.Directory.GetCurrentDirectory())
        DotNet.pack (fun p -> { p with OutputPath = Some destDir }) "thinkerino.cs/thinkerino.cs.csproj"
    )
    Target.create "bumpVersion.cs" (fun _ -> FakeVar.getOrFail "newVersion" |> applyVersion)
    // "install.cs" ==> "install" |> ignore
    "clean.cs" ?=> "build.cs" ?=> "test.cs" |> ignore
    "clean.cs" ==> "clean" |> ignore
    "build.cs" ==> "build" |> ignore
    "test.cs" ==> "test" |> ignore
    "build.cs" ==> "release.cs" ==> "release" |> ignore
    "calculatePatch" ?=> "bumpVersion.cs" ==> "bumpPatch" |> ignore
    "calculateMinor" ?=> "bumpVersion.cs" ==> "bumpMinor" |> ignore
    "calculateMajor" ?=> "bumpVersion.cs" ==> "bumpMajor" |> ignore