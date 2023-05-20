module Thinkerino.Build.Python

open Fake.Core
open Fake.IO
open Fake.Core.TargetOperators
open Fake.DotNet

open Thinkerino.Build.Utils

let init () =
    Target.create "install.py" (fun _ ->
        let venvExists =
            (Path.combine "thinkerino.py" ".venv"
             |> DirectoryInfo.ofPath
             |> DirectoryInfo.exists)

        if not venvExists then
            Trace.log ("Creating virtual environment for python, since it's missing!")

            CreateProcess.fromRawCommand "python3" [ "-m"; "venv"; "thinkerino.py/.venv" ]
            |> Proc.run
            |> ignore

        CreateProcess.fromRawCommand
            "thinkerino.py/.venv/bin/python3"
            [ "-m"
              "pip"
              "install"
              "-r"
              "thinkerino.py/requirements-dev.txt" ]
        |> Proc.run
        |> ignore

        CreateProcess.fromRawCommand
            "thinkerino.py/.venv/bin/python3"
            [ "-m"
              "pip"
              "install"
              "-e"
              "thinkerino.py" ]
        |> Proc.run
        |> ignore)

    Target.create "clean.py" (fun _ ->
        [ "lib"; "dist"; "build" ]
        |> List.map (fun folder ->
            Path.combine "thinkerino.py" folder
            |> Directory.delete)
        |> ignore)

    Target.create "build.py" (fun _ ->
        let res =
            DotNet.exec
                (fun _ -> DotNet.Options.Create())
                "fable"
                "thinkerino/thinkerino.fsproj -o ./thinkerino.py/lib --lang Python"

        if res.ExitCode <> 0 then
            failwithf "Python build failed: %A" (res.Errors)

    )


    Target.create "test.py" (fun _ ->
        let res =
            CreateProcess.fromRawCommand "thinkerino.py/.venv/bin/python3" [ "-m"; "pytest"; "thinkerino.py/" ]
            |> Proc.run

        if res.ExitCode <> 0 then
            failwithf "Python tests failed: %A" (res.Result))

    Target.create "release.py" (fun _ ->
        let semVer = getSemVer ()
        File.replaceContent "thinkerino.py/VERSION" semVer

        CreateProcess.fromRawCommand "thinkerino.py/.venv/bin/python3" [ "setup.py"; "bdist" ]
        |> CreateProcess.withWorkingDirectory "thinkerino.py/"
        |> Proc.run
        |> ignore)

    "install.py" ==> "install" |> ignore
    "clean.py" ?=> "build.py" ?=> "test.py" |> ignore
    "clean.py" ==> "clean" |> ignore
    "build.py" ==> "build" |> ignore
    "test.py" ==> "test" |> ignore

    "build.py" ==> "release.py" ==> "release"
    |> ignore
