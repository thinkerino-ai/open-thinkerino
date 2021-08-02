module AITools.Proofs.Language
open AITools.Logic.Language
open AITools.Logic.Utils

let private language = Language()

let And = makeNamed language ConstExpr "And"
let Or = makeNamed language ConstExpr "Or"
let Implies = makeNamed language ConstExpr "Implies"
let CoImplies = makeNamed language ConstExpr "CoImplies"
let Not = makeNamed language ConstExpr "Not"