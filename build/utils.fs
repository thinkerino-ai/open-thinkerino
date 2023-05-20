module Thinkerino.Build.Utils
open Fake.Tools

let getSemVer() = (GitVersion.generateProperties (fun cfg ->
                { cfg with
                    ToolPath = "dotnet-gitversion"
                    ToolType = Fake.DotNet.ToolType.CreateLocalTool() }))                .FullSemVer