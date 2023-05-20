# open-thinkerino

This is the open-source version of Thinkerino! What is it? Did you see it in the shadow?

My main advice is... don't use it for now :D

I O U one nice description :P

## How to build

```sh
dotnet tool restore
dotnet paket restore
dotnet run --project build install
dotnet run --project build reretest
# alternatively ./build.sh reretest
```

Possible targets for building are listed in the `build` project (each file defines some targets, though the main ones are `main.fs` and `watch.fs`), but typically you'll want one of `test`, or `watch`; `retest` runs a normal build before running tests, `reretest` runs a clean build before running tests.

## Useful commands

To add a dependency with paket

```sh
dotnet paket add -p projectName dependency
```