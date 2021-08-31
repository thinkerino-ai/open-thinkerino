module Thinkerino.Proofs.Language
open Thinkerino.Logic.Language
open Thinkerino.Logic.Utils

let private language = Language()

let And = makeNamed language ConstExpr "And"
let Or = makeNamed language ConstExpr "Or"
let Implies = makeNamed language ConstExpr "Implies"
let CoImplies = makeNamed language ConstExpr "CoImplies"
let Not = makeNamed language ConstExpr "Not"