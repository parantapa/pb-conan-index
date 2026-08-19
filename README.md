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
| `gurobi` | `13.0.0.pci` | <https://www.gurobi.com> |
| `ortools` | `9.15.pci` | <https://github.com/google/or-tools> |
| `random123` | `1.14.0.pci` | <https://github.com/DEShawResearch/random123> |
| `taskflow` | `4.1.0.pci` | <https://github.com/taskflow/taskflow> |
| `zpp_bits` | `4.7.6.pci` | <https://github.com/eyalz800/zpp_bits> |

Every version carries a `.pci` suffix.
It marks the recipe as packaged by this index,
and keeps it apart from a recipe of the same name and version elsewhere;
conancenter, for instance, ships its own `taskflow` and `zpp_bits`.

## Layout

Each package lives under `recipes/<package>`:

```
recipes/<package>/config.yml            versions and the folder that builds them
recipes/<package>/all/conanfile.py      the recipe
recipes/<package>/all/conandata.yml     source urls and checksums, when the recipe fetches an archive
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
The other packages use the conan defaults,
so `random123` is `find_package(random123)` and `random123::random123`.
