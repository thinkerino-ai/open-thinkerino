namespace Thinkerino

open Thinkerino.Logic.Language
open Thinkerino.Logic.Core
open Thinkerino.Logic.Unification
open Thinkerino.Logic.Utils

module Say =
    let hello name = sprintf "Hello %s" name


    let test () = 
        let lang = Language(System.Guid(), true)

        let a =
            Constant(Identifier(lang, lang.GetNext()), Some "a")

        let b = makeNamed lang Constant "b"

        let x = makeNamed lang Variable "x"

        let expr1 = Expr [| Const a; Const b; Var x |]
        let expr2 = Expr [| Const a; Const b; Const a |]

        let unifier = Substitution.Unify(expr1, expr2)

        let res = unifier.Value.ApplyTo(expr1)

        res