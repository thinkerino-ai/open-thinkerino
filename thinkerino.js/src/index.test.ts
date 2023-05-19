import { helloAPI, runTest } from './index'

describe('index module', () => {
    test('prova', () => {
        expect(helloAPI('gigi')).toBe("Hello gigi")
    })
    test('prova2', () => {
        const res = runTest()
        console.log('res: ', res)
    })
})
