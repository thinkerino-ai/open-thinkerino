import { hello, test } from "../lib/Library"


export const helloAPI: (name: string) => string = hello

export const runTest = test

// TODO fix typing
export const makeExpr = expr => {
    if (Array.isArray(expr))
        return expr.map(makeExpr)
}
