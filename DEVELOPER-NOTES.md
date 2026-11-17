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
  with the cmake on `PATH`,
  and those that build against other recipes generate them with `CMakeDeps`.
  `kokkos` needs cmake 3.22 or newer, from the system or from `tool_requires`.
  `validate` checks a `tool_requires` cmake,
  and `build` checks the cmake that the build environment runs.
- Make and configure: `gurobi` builds with `make`.
  `upcxx` runs its own `configure` and then `make`,
  without `AutotoolsToolchain`.
  `papi` runs its own `configure` and then `make` in the source tree,
  with the environment that `AutotoolsToolchain` writes.
  The header only recipes have no build step.
- pkg-config: `upcxx` asks pkg-config for the install prefix
  of the system `pmix` and `hwloc`.
  `kokkos` asks it for the library and header folders of `hwloc`.
  `cryptominisat5`, `arjun`, `approxmc` and `ganak`
  find `gmp`, `mpfr` and `flint` through `pkg_check_modules`.
  Those four recipes generate `.pc` files with `PkgConfigDeps`,
  and take `pkgconf` as a tool requirement.
  `upcxx` and `kokkos` run the pkg-config of the system.
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
This binds `clingo`, `libtorch`, `ortools`, `rapidcheck`, `upcxx`, `z3`,
and every recipe of the ganak family.
`libtorch` renames `share/cmake`,
but deletes `lib/cmake`.

`kokkos` is the exception.
Its consumers use the upstream package files,
and CMakeDeps generates nothing for it.
The upstream files put the backend and architecture flags on the targets
inside generator expressions.
They find CUDAToolkit, OpenMP and hwloc,
and they define `kokkos_check` and `kokkos_compilation`.
In a CUDA build, they also set `RULE_LAUNCH_COMPILE`
to `kokkos_launch_compiler`,
which sends every compile that uses Kokkos through `nvcc_wrapper`.
CMakeDeps can express none of this.
The recipe sets `cmake_find_mode` to `none`,
and puts `lib/cmake/Kokkos` in the `builddirs` of the `kokkoscore` component.
CMakeToolchain reads `builddirs` from the components only,
once a package has components.
The cost is that the package files must work from any folder.
The only absolute path upstream writes into them
is a second hint for `nvcc_wrapper` in `KokkosConfigCommon.cmake`,
and `package()` removes it.
See "The install prefix check".

### The library directory

The recipes this section binds
set `CMAKE_INSTALL_LIBDIR` to `lib`.
GNUInstallDirs otherwise picks `lib64` on 64-bit non-Debian Linux,
which is outside the directories the recipe reports to consumers.
This binds `clingo`, `kokkos`, `libtorch`, `ortools`,
and every recipe of the ganak family.

### The install prefix check

A recipe whose upstream install writes the install prefix into files
checks the package at the end of `package()`.
`_check_relocatable` fails the package build
if any file still holds the absolute package folder.
A new option or upstream release that installs another such file
then fails the build,
instead of shipping a package that only works in one folder.
The cost is that `package()` reads every file of the package once.
`kokkos` and `upcxx` skip a file that holds a NUL byte,
because a binary carries their prefix only in debug and ident strings.
`upcxx` also skips `upcxx_config.hpp` and `config-details.txt`,
which only record the configure command.
`papi` reads its binaries too,
so that the check also catches a run path to the prefix.
This binds `package()` of `kokkos`, `papi` and `upcxx`.

### The meelgroup dependency lookup

The libraries of the ganak family find each other
through a `<name>_DIR` cache variable.
Where the variable is empty,
upstream fetches the dependency with FetchContent from its default branch.
Each recipe sets the variable of every dependency that upstream looks up this way
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

### The libtorch force link

On Linux and FreeBSD, a shared `libtorch` package force links `libtorch.so`.
`package_info` puts `-Wl,--no-as-needed,<path to libtorch.so>`
and then `-Wl,--as-needed` in both `exelinkflags` and `sharedlinkflags`.
`libtorch` is a shim with no code of its own that a consumer references.
It carries a `DT_NEEDED` on `torch_cpu` and `c10`,
and with CUDA on `torch_cuda` and `c10_cuda`.
The linker default of `--as-needed` therefore drops it,
and everything reachable only through it goes with it.
What that costs is the registration that runs from static initializers.
With `torch_cuda` dropped, nothing installs the CUDA hooks,
and `torch::cuda::is_available()` answers false
on a machine with a working GPU.
Upstream hits this too,
and force links the same way in the `torch` target of its own `Caffe2Targets.cmake`.
The cost is that `-Wl,--as-needed` is switched back on after the shim,
whatever the consumer had set before it.
This binds `package_info` of `libtorch`.

### The hdf5_plugins against a static hdf5

hdf5 loads a filter into a process that already runs hdf5.
A static hdf5 linked into the filter
puts a second copy of the library in that process.
A filter that calls back into hdf5 from its `set_local` callback
then fails to recognize the property list of the caller.
Linking hdf5 into each filter is therefore rejected.
Against a static hdf5, `generate()` gives the filters the hdf5 headers
through an interface target, and no hdf5 to link.
The filters are built with the hdf5 symbols left undefined,
and the process that loads them resolves those symbols.
That lookup only finds them
if the program put its own symbols in the dynamic symbol table.
`package_info` asks for that with `-rdynamic` on Linux and FreeBSD,
and with `-Wl,-export_dynamic` on macOS, in `exelinkflags`,
so a consumer needs no change of its own.
A dll cannot leave symbols undefined,
so `validate` rejects a static hdf5 on Windows.
The cost is that every consumer executable exports all its symbols.
The recipe therefore defaults to `hdf5/*:shared=True`,
and against a shared hdf5 the filters link `hdf5::hdf5` as usual.
This binds `default_options`, `validate`, `generate` and `package_info`
of `hdf5_plugins`.

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
- `bin/upcxx` follows a symbolic link to itself with `readlink`,
  and then finds its folder with `cd -P`.
  `test-upcxx-install.sh` finds the package folder with `cd -P`
  from the folder of `$0`.
- The GASNet-EX `.pc` files use `${pcfiledir}`,
  and the `.mak` files compute `GASNET_PREFIX` from `MAKEFILE_LIST`.
- The modulefile computes the prefix from `[info script]`.

`upcxx_config.hpp` and `config-details.txt` keep the absolute install prefix.
They only record the configure command.
After the rewrite, `package()` checks the package,
as "The install prefix check" describes.
`package()` collects the flags through the rewritten `bin/upcxx-meta`,
so every package build also runs the relocated scripts.
