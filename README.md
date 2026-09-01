# pb-conan-index

PB's personal conan recipes index.

This repository holds conan recipes for packages
that are either missing from conancenter,
or that are needed in a version or configuration conancenter does not provide.
It follows the same layout as
[conan-center-index](https://github.com/conan-io/conan-center-index),
so conan can consume it directly as a local recipes index remote.

## Recipes

| Package | Version | Upstream |
| --- | --- | --- |
| `clingo` | `5.8.2.pci` | <https://github.com/potassco/clingo> |
| `gurobi` | `13.0.0.pci` | <https://www.gurobi.com> |
| `hdf5_plugins` | `2.2.0.pci` | <https://github.com/HDFGroup/hdf5_plugins> |
| `ortools` | `9.15.pci` | <https://github.com/google/or-tools> |
| `random123` | `1.14.0.pci` | <https://github.com/DEShawResearch/random123> |
| `rapidcheck` | `20260806.pci` | <https://github.com/emil-e/rapidcheck> |
| `taskflow` | `4.1.0.pci` | <https://github.com/taskflow/taskflow> |
| `z3` | `5.1.0.pci` | <https://github.com/Z3Prover/z3> |
| `zpp_bits` | `4.7.6.pci` | <https://github.com/eyalz800/zpp_bits> |

Every version carries a `.pci` suffix.
It marks the recipe as packaged by this index,
and keeps it apart from a recipe of the same name and version elsewhere;
conancenter, for instance, ships its own `taskflow` and `zpp_bits`.

`rapidcheck` has no upstream releases,
so its version is the date of the git revision the recipe pins.

The `z3` recipe packages the C and C++ library only;
the z3 executable and the python, java, dotnet, julia, ocaml
and go bindings are not built.

The `ortools` recipe packages the C++ library only.
It builds the BOP, GLOP, PDLP and MathOpt solvers,
leaves COIN-OR, GLPK, HiGHS, SCIP and CPLEX out,
and does not build the flatzinc front end
or the python, java and dotnet bindings.

The `clingo` recipe packages the C and C++ library.
Its `apps` option, off by default,
additionally builds the clingo, gringo, clasp, reify and lpconvert
executables into `bin`.
The bundled clasp and potassco are built along with it,
so the package pulls in no other recipe.

The `hdf5_plugins` recipe packages the compression filters
that hdf5 loads at run time.
It builds the bitgroom, bitround, blosc, blosc2, bshuf, bzip2,
granular_bitround, jpeg, lz4, lzf, zfp and zstd filters,
each behind an option of its own that is on by default.
Every filter takes its compression library
from the source the release tarball bundles
and links it in statically,
so the package needs no recipe other than `hdf5`.

A filter is loaded into a process that already runs hdf5,
so the linkage of that hdf5 reaches into the filters themselves.
Against a shared hdf5 they link it as well.
Against a static one they are built with the hdf5 symbols left undefined
and resolve them against the program that loads them,
which only works if that program exports its own symbols;
the recipe asks for that through a link flag,
so a consumer needs no change of its own.

## Layout

Each package lives under `recipes/<package>`:

```
recipes/<package>/config.yml            versions and the folder that builds them
recipes/<package>/all/conanfile.py      the recipe
recipes/<package>/all/conandata.yml     per version source data: archive url and checksum, or git revision
```

## Setup

Requires conan 2.2 or newer for the local recipes index remote.

Clone the repository and register it as a remote:

```sh
git clone https://github.com/taskflow/taskflow
conan remote add pb-conan-index /path/to/pb-conan-index --type=local-recipes-index
```

Check that conan sees the recipes:

```sh
conan list "*" -r=pb-conan-index
```

Pull updates with `git pull`;
the remote reads the working tree, so no further conan command is needed.

## Usage

Require the packages as usual, for example in a `conanfile.txt`:

```ini
[requires]
taskflow/4.1.0.pci
zpp_bits/4.7.6.pci

[generators]
CMakeDeps
CMakeToolchain
```

Then build the dependencies, since this index serves recipes only:

```sh
conan install . --build=missing
```

In CMake, `taskflow` is found as `find_package(Taskflow)`
and linked as `Taskflow::Taskflow`.
`rapidcheck` is found as `find_package(rapidcheck)`
and linked as `rapidcheck`, without a namespace,
matching the target upstream exports.
`z3` is found as `find_package(Z3)`
and linked as `z3::libz3`.
`clingo` is found as `find_package(Clingo)`
and linked as `libclingo`, without a namespace,
matching the target upstream exports.
The other packages use the conan defaults,
so `random123` is `find_package(random123)` and `random123::random123`.

`hdf5_plugins` has no cmake target and nothing to link against.
It adds its plugin directory to `HDF5_PLUGIN_PATH` instead,
so hdf5 finds the filters
as soon as a `VirtualRunEnv` or `VirtualBuildEnv` environment is active.
