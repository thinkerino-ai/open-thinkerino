module Thinkerino.Build.JavaScript

open Fake.Core
open Fake.Core.TargetOperators
open Thinkerino.Build.Utils

let applyVersion version =
    Fake.JavaScript.Npm.run (sprintf "set-version %s" version) (fun o -> { o with WorkingDirectory = "./thinkerino.js" })

let init () =
    Target.create "install.js" (fun _ ->
        Fake.JavaScript.Npm.install (fun o -> { o with WorkingDirectory = "./thinkerino.js" }))

    Target.create "clean.js" (fun _ ->
        Fake.JavaScript.Npm.run "clean" (fun o -> { o with WorkingDirectory = "./thinkerino.js" }))


    Target.create "build-lib.js" (fun _ ->
        Fake.JavaScript.Npm.run "build-lib" (fun o -> { o with WorkingDirectory = "./thinkerino.js" }))

    Target.create "build-src.js" (fun _ ->
        Fake.JavaScript.Npm.run "build-src" (fun o -> { o with WorkingDirectory = "./thinkerino.js" }))

    Target.create "build.js" ignore

    Target.create "test.js" (fun _ ->
        Fake.JavaScript.Npm.run "test" (fun o -> { o with WorkingDirectory = "./thinkerino.js" }))

    Target.create "retest.js" ignore

    Target.create "release.js" (fun _ ->
        let semVer = getSemVer ()

        applyVersion semVer

        let destination = sprintf "%s/dist/javascript" (System.IO.Directory.GetCurrentDirectory())
        Fake.IO.Directory.ensure(destination)
        let command =
            sprintf "pack --pack-destination=%s" destination

        Fake.JavaScript.Npm.exec command (fun o -> { o with WorkingDirectory = "thinkerino.js" }))

    Target.create "bumpVersion.js" (fun _ -> FakeVar.getOrFail "newVersion" |> applyVersion)

    "install.js" ==> "install" |> ignore

    "clean.js"
    ?=> "build-lib.js"
    ?=> "build-src.js"
    ?=> "build.js"
    ?=> "test.js"
    |> ignore

    "clean.js" ==> "clean" |> ignore
    "build-lib.js" ==> "build.js" |> ignore
    "build-src.js" ==> "build.js" |> ignore
    "build.js" ==> "build" |> ignore
    "test.js" ==> "test" |> ignore
    "test.js" ==> "retest.js" |> ignore
    "build-src.js" ==> "retest.js" |> ignore

    "build.js" ==> "release.js" ==> "release"
    |> ignore

    "calculatePatch" ?=> "bumpVersion.js"
    ==> "bumpPatch"
    |> ignore

    "calculateMinor" ?=> "bumpVersion.js"
    ==> "bumpMinor"
    |> ignore

    "calculateMajor" ?=> "bumpVersion.js"
    ==> "bumpMajor"
    |> ignore
