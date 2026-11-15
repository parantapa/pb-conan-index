# Developer notes

## Map of the source

- `recipes/<package>/config.yml` maps each version to the folder that builds it.
  Every package has one folder, `all`.
- `recipes/<package>/all/conanfile.py` is the recipe.
  Conan loads it by path, and nothing else in the repository imports it.
- `recipes/<package>/all/conandata.yml` holds the source data per version:
  an archive url and checksum, or a git url with a tag or a commit.
  `random123` has none, because its recipe clones the tag itself.
- The ganak family is `ganak` and the seven recipes it requires:
  `cadical`, `cadiback`, `cryptominisat5`, `sbva`, `treedecomp`, `arjun` and `approxmc`.
  `ganak` pins its release tag,
  and the seven pin the revisions that the `flake.lock` of that release names.
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
When the profile sets a lower standard,
a recipe whose `validate` asks for C++20 also needs `-s compiler.cppstd=20`.

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
  `upcxx` runs its own `configure` and then `make`,
  and the header only recipes have no build step.
- pkg-config: `upcxx` asks pkg-config for the install prefix
  of the system `pmix` and `hwloc`.
  `cryptominisat5`, `arjun`, `approxmc` and `ganak`
  find `gmp`, `mpfr` and `flint` through `pkg_check_modules`.
  These recipes generate `.pc` files with `PkgConfigDeps`,
  and take `pkgconf` as a tool requirement.
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
This binds `clingo`, `libtorch`, `ortools`, `rapidcheck`, `z3`,
and every recipe of the ganak family.

### The library directory

A recipe that builds with CMake and installs libraries
sets `CMAKE_INSTALL_LIBDIR` to `lib`.
GNUInstallDirs otherwise picks `lib64` on 64-bit non-Debian Linux,
which is outside the directories the recipe reports to consumers.
This binds `clingo`, `libtorch`, `ortools`,
and every recipe of the ganak family.

### The meelgroup dependency lookup

The libraries of the ganak family find each other
through a `<name>_DIR` cache variable.
Where the variable is empty,
upstream fetches the dependency with FetchContent from its default branch.
Each recipe sets the variable of every dependency
to the generators folder, where CMakeDeps writes the config files.
Each recipe also sets `FETCHCONTENT_FULLY_DISCONNECTED`,
so a lookup that misses the variables fails at configure time
instead of downloading a moving branch.
The cost is one cache variable per dependency in every recipe.
This binds `cadiback`, `cryptominisat5`, `arjun`, `approxmc` and `ganak`.

### The static library suffix order

`arjun`, `approxmc` and `ganak` set `CMAKE_FIND_LIBRARY_SUFFIXES`
to prefer `.a` whenever they build static.
The `mpfr.pc` that PkgConfigDeps writes requires all of gmp,
and `gmpxx.pc` adds `-lm`.
`pkg_check_modules` then resolves that `-lm` to the `libm.a` of glibc,
which fails to link into a dynamic executable.
Conan already gives every dependency by its full path,
so the recipes delete that line in `source()`.
`cryptominisat5` sets the same order,
but it asks pkg-config for `gmp` alone, which adds no system library,
so its recipe leaves the line in place.

### The upcxx flags file

The `upcxx` recipe does not report flags
by running `upcxx-meta` in `package_info`.
That would cost a shell process for every consumer of the package.
`package()` runs `bin/upcxx-meta` once for every code mode,
thread mode and network instead.
It records the flags in `share/conan/upcxx-flags.json`,
with every path inside the package made relative to the package folder.
`package_info` reads the entry that `build_type`, `threadmode` and `network` select.
The cost is a parser of the `upcxx-meta` output in the recipe.
It drops the GASNet-EX optimization and warning flags,
and the `libgcc` that the compiler links on its own.

The recipe calls `configure` itself instead of using `AutotoolsToolchain`.
It also unsets `CFLAGS`, `CXXFLAGS`, `CPPFLAGS`, `LDFLAGS` and `LIBS`.
UPC++ passes those to every code mode it builds,
where they would replace the flags that tell the debug and opt code modes apart.

### The upcxx relocation

The UPC++ install writes its absolute prefix into the scripts it installs.
`package()` rewrites every file that reads the prefix back,
so that the package works from any folder.

- The outer `bin/upcxx-meta` takes the prefix from `BASH_SOURCE`,
  and exports it as `UPCXXI_INSTALL_PREFIX`.
  It does not fork, because upstream keeps its `DUMP` branch free of forks.
- Each inner `upcxx-meta` refers to the prefix
  as the token `${UPCXXI_INSTALL_PREFIX:?}`.
  The token expands when bash sources the script,
  and when `/bin/sh` runs it with the variable in the environment.
  A single quoted value becomes double quoted, so that it expands.
  An inner script run on its own fails instead of printing paths under `/`.
- `DUMP` prints the inner script for its caller to evaluate,
  so it puts the prefix itself in place of the token.
- `bin/upcxx` and `test-upcxx-install.sh` find their folder with `cd -P`,
  which follows a symbolic link back into the package.
- The GASNet-EX `.pc` files use `${pcfiledir}`,
  and the `.mak` files compute `GASNET_PREFIX` from `MAKEFILE_LIST`.
- The modulefile computes the prefix from `[info script]`.

`upcxx_config.hpp` and `config-details.txt` keep the build path.
They only record the configure command.
After the rewrite, `package()` fails
if any other text file still holds the prefix.
A new conduit, option or upstream release
that installs another such file then fails the package build,
instead of shipping a package that only works in one folder.
`package()` collects the flags through the rewritten `bin/upcxx-meta`,
so every package build also runs the relocated scripts.
