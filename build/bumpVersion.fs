module Thinkerino.Build.BumpVersion

open Fake.Core
open Fake.Core.TargetOperators
open Thinkerino.Build.Utils
open Fake.Tools

let commitAndTag () =
    let newVersion = FakeVar.getOrFail "newVersion"
    Git.Staging.stageAll "."
    let tag = sprintf "v%s" newVersion
    let commitMessage = sprintf "Bump version to %s" tag
    Git.Commit.exec "." commitMessage
    Git.Branches.tag "." tag


let init () =
    Target.create "ensureCleanWorkingCopy" (fun _ ->
        if not (Git.Information.isCleanWorkingCopy ".") then
            failwithf "Working copy is not clean!")

    Target.create
        "calculatePatch"
        (ignore
         >> getSemVer
         >> bumpVersion "patch"
         >> FakeVar.set "newVersion")

    Target.create
        "calculateMinor"
        (ignore
         >> getSemVer
         >> bumpVersion "minor"
         >> FakeVar.set "newVersion")

    Target.create
        "calculateMajor"
        (ignore
         >> getSemVer
         >> bumpVersion "major"
         >> FakeVar.set "newVersion")

    Target.create "bumpPatch" (ignore >> commitAndTag)
    Target.create "bumpMinor" (ignore >> commitAndTag)
    Target.create "bumpMajor" (ignore >> commitAndTag)

    "ensureCleanWorkingCopy" ==> "calculatePatch" ==> "bumpPatch" |> ignore
    "ensureCleanWorkingCopy" ==>"calculateMinor" ==> "bumpMinor" |> ignore
    "ensureCleanWorkingCopy" ==>"calculateMajor" ==> "bumpMajor" |> ignore
