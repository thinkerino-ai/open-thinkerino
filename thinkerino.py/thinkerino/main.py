from lib.library import hello, test

def helloAPI(name: str):
    return hello(name)

def runTest():
    return test()

__all__ = ['helloAPI']
# import { hello } from "../lib/Library"

# export const helloAPI: (name: string) => string = hello
# console.log(hello("amico"))