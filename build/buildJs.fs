module Thinkerino.Build.JavaScript
open Fake.Core
open Fake.Core.TargetOperators

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
