/*
 * For a detailed explanation regarding each configuration property and type check, visit:
 * https://jestjs.io/docs/configuration
 */

const { pathsToModuleNameMapper } = require('ts-jest')
// In the following statement, replace `./tsconfig` with the path to your `tsconfig` file
// which contains the path mapping (ie the `compilerOptions.paths` option):
const { compilerOptions } = require('./tsconfig.json')


/** @type {import('ts-jest').JestConfigWithTsJest} */
// old from ts-jest
// module.exports = {
//   preset: 'ts-jest',
//   testEnvironment: 'node',

// };
module.exports = {
  preset: 'ts-jest/presets/js-with-ts',
  rootDir: 'src',
};
