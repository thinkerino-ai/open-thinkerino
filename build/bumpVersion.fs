module Thinkerino.Build.BumpVersion

open Fake.Core
open Fake.Core.TargetOperators
open Thinkerino.Build.Utils

let init () =
    Target.create "calculatePatch" (ignore >> getSemVer >> bumpVersion "patch" >> FakeVar.set "newVersion")

    Target.create "calculateMinor" (ignore >> getSemVer >> bumpVersion "minor" >> FakeVar.set "newVersion")
    Target.create "calculateMajor" (ignore >> getSemVer >> bumpVersion "major" >> FakeVar.set "newVersion")
    Target.create "bumpPatch" ignore
    Target.create "bumpMinor" ignore
    Target.create "bumpMajor" ignore

    "calculatePatch" ==> "bumpPatch" |> ignore
    "calculateMinor" ==> "bumpMinor" |> ignore
    "calculateMajor" ==> "bumpMajor" |> ignore