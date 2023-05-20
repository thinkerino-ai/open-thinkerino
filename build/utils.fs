module Thinkerino.Build.Utils

open Fake.Core
open Fake.Tools

let getSemVer () =
    (GitVersion.generateProperties (fun cfg ->
        { cfg with
            ToolPath = "dotnet-gitversion"
            ToolType = Fake.DotNet.ToolType.CreateLocalTool() }))
        .FullSemVer

let bumpVersion (part: string) (version: string) =
    let parsedVersion = SemVer.parse version

    let newVersion =
        match part.ToLower() with
        | "major" ->
            { parsedVersion with
                Major = parsedVersion.Major + 1u
                Minor = 0u
                Patch = 0u
                Original = None }
        | "minor" ->
            { parsedVersion with
                Minor = parsedVersion.Minor + 1u
                Patch = 0u
                Original = None }
        | "patch" ->
            { parsedVersion with
                Patch = parsedVersion.Patch + 1u
                Original = None }
        | _ -> failwith "Invalid part specified. Use 'major', 'minor', or 'patch'."

    newVersion.AsString
