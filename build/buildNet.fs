module Thinkerino.Build.DotNet
open Fake.Core
open Fake.Core.TargetOperators
open Fake.DotNet
open Thinkerino.Build.Utils

let applyVersion = Xml.pokeInnerText "thinkerino/thinkerino.fsproj" "/Project/PropertyGroup/Version"

let init () =
    // TODO remove this since I switched to paket (also below)
    //Target.create "install.net" (fun _ -> DotNet.restore id "./thinkerino")

    Target.create "clean.net" (fun _ ->
        DotNet.exec (DotNet.Options.withWorkingDirectory "./thinkerino") "clean" ""
        |> ignore)


    Target.create "build.net" (fun _ -> DotNet.build (DotNet.Options.withWorkingDirectory "./thinkerino") "")

    Target.create "test.net" (fun _ ->
        let res =
            DotNet.exec (DotNet.Options.withWorkingDirectory "./tests") "run" ""

        if res.ExitCode <> 0 then
            failwithf "Dotnet tests failed: %A" (res.Results)

    )

    Target.create "release.net" (fun _ ->
        let semVer = getSemVer ()

        applyVersion semVer

        DotNet.pack id "thinkerino/thinkerino.fsproj"
    )
    Target.create "bumpVersion.net" (fun _ -> FakeVar.getOrFail "newVersion" |> applyVersion)
    // "install.net" ==> "install" |> ignore
    "clean.net" ?=> "build.net" ?=> "test.net" |> ignore
    "clean.net" ==> "clean" |> ignore
    "build.net" ==> "build" |> ignore
    "test.net" ==> "test" |> ignore
    "build.net" ==> "release.net" ==> "release" |> ignore
    "calculatePatch" ?=> "bumpVersion.net" ==> "bumpPatch" |> ignore
    "calculateMinor" ?=> "bumpVersion.net" ==> "bumpMinor" |> ignore
    "calculateMajor" ?=> "bumpVersion.net" ==> "bumpMajor" |> ignore