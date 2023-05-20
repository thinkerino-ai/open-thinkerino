module Thinkerino.Build.CSharp
open Fake.Core
open Fake.Core.TargetOperators
open Fake.DotNet

open Thinkerino.Build.Utils

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

        Xml.pokeInnerText "thinkerino.cs/thinkerino.cs.csproj" "/Project/PropertyGroup/Version" semVer
        DotNet.pack id "thinkerino.cs/thinkerino.cs.csproj"
    )
    // "install.cs" ==> "install" |> ignore
    "clean.cs" ?=> "build.cs" ?=> "test.cs" |> ignore
    "clean.cs" ==> "clean" |> ignore
    "build.cs" ==> "build" |> ignore
    "test.cs" ==> "test" |> ignore
    "build.cs" ==> "release.cs" ==> "release" |> ignore