import typescript from 'rollup-plugin-ts';

export default {
  input: 'src/index.ts',
  output: {
    dir: 'dist',
    format: 'esm',
  },
  plugins: [typescript()]
};