# Developer notes

## Map of the source

- `recipes/<package>/config.yml` maps each version to the folder that builds it.
  Every package has one folder, `all`.
- `recipes/<package>/all/conanfile.py` is the recipe.
  Conan loads it by path, and nothing else in the repository imports it.
- `recipes/<package>/all/conandata.yml` holds the source data per version:
  an archive url and checksum, or a git url with a tag or a commit.
  `random123` has none, because its recipe clones the tag itself.
- `docs/` holds the user documentation.
  `docs/reference/recipes.md` describes what each recipe packages,
  and changes with any recipe change that a consumer can see.
- `.cpush.json5` names the project and one remote,
  `rivanna:pb-conan-index`, for the `cpush` tool.

## Build and run

The recipes assume conan 2.2 or newer,
which is the first release with the local recipes index remote.

Build one package from its recipe:

```sh
conan create recipes/<package>/all --version <version> --build=missing
```

`<version>` is a key of `recipes/<package>/config.yml`,
with its `.pci` suffix, as in `4.1.0.pci`.

To consume the recipes from the working tree,
register the repository as a remote, as the README shows.
The remote reads the working tree,
so an edited recipe is visible without another conan command.

## Tests

No recipe has a `test_package`, and the repository has no test suite.
`conan create` on the changed recipe is the check for a change.

## Formatter and type checker

The project has no formatter or type checker configuration of its own.
Format with black, then check with pyright.
Every `conanfile.py` starts with `# type: ignore`,
so pyright reports nothing for these files.

## Tools and libraries

- Conan 2: every recipe subclasses `ConanFile`
  and uses the helpers in `conan.tools`.
- CMake: most recipes build through `CMakeToolchain` and `CMake`,
  and those that build against other recipes generate them with `CMakeDeps`.
  `gurobi` builds with `make`,
  and the header only recipes have no build step.
- Git: `libtorch`, `random123` and `rapidcheck` clone their source
  through `conan.tools.scm.Git` instead of downloading an archive.

## Design decisions

### The `.pci` version suffix

Every version in `config.yml` carries a `.pci` suffix.
It keeps a recipe of this index apart from a conancenter recipe
of the same name and version.
The cost is that a recipe strips the suffix
wherever it needs the upstream version,
as in a tag name or a library file name.
This binds `gurobi`, `hdf5_plugins` and `random123`.

### The upstream cmake package files

A recipe whose upstream installs cmake package files
renames their folder to `_orig_cmake` in `package()`,
instead of deleting it.
CMakeDeps generates the package files a consumer uses.
The rename keeps the upstream files out of the cmake search path,
and they stay in the package.
This binds `clingo`, `libtorch`, `ortools`, `rapidcheck` and `z3`.

### The library directory

A recipe that builds with CMake and installs libraries
sets `CMAKE_INSTALL_LIBDIR` to `lib`.
GNUInstallDirs otherwise picks `lib64` on 64-bit non-Debian Linux,
which is outside the directories the recipe reports to consumers.
This binds `clingo`, `libtorch` and `ortools`.
