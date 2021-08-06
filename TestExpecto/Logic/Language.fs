module Thinkerino.Tests.Logic.Language

open Expecto
open AITools.Logic.Language
open System

[<Tests>]
let languageTests =
    testList
        "language module"
        [

          test "Language generates sequential ids" {
              let language = Language()

              Expect.equal (language.GetNext()) 1L "first id has is 1"
              Expect.equal (language.GetNext()) 2L "second id is 2"
              Expect.equal (language.GetNext()) 3L "third id is 3"


          }
          test "Language equality is based on its id" {
              let commonGuid =
                  System.Guid("00000000-0000-0000-0000-000000000042")

              let languageA =
                  Language(languageId = commonGuid, enabled = true)

              let languageB =
                  Language(languageId = commonGuid, enabled = true)

              // the two languages have different
              languageA.GetNext() |> ignore
              languageB.GetNext() |> ignore
              languageB.GetNext() |> ignore

              Expect.equal languageA languageB "language equality only depends on the language id"
              Expect.equal (hash languageA) (hash commonGuid) "language hash only depends on the id"
              Expect.equal (hash languageB) (hash commonGuid) "language hash only depends on the id"

          }
          test "Language string representation" {
              let someGuid =
                  Guid("00000000-0000-0000-0000-000000000042")

              let someLanguage =
                  Language(languageId = someGuid, enabled = true)

              Expect.equal
                  "Language(00000000-0000-0000-0000-000000000042)"
                  (string someLanguage)
                  "language representation is correct"
          } ]
