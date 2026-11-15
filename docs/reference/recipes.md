# Recipes

| Package | Version | Upstream |
| --- | --- | --- |
| `approxmc` | `4.3.4.pci` | <https://github.com/meelgroup/approxmc> |
| `arjun` | `2.9.0.pci` | <https://github.com/meelgroup/arjun> |
| `cadiback` | `20260912.pci` | <https://github.com/meelgroup/cadiback> |
| `cadical` | `20260912.pci` | <https://github.com/meelgroup/cadical> |
| `clingo` | `5.8.2.pci` | <https://github.com/potassco/clingo> |
| `cryptominisat5` | `5.16.0.pci` | <https://github.com/msoos/cryptominisat> |
| `ganak` | `2.7.0.pci` | <https://github.com/meelgroup/ganak> |
| `gurobi` | `13.0.0.pci` | <https://www.gurobi.com> |
| `hdf5_plugins` | `2.2.0.pci` | <https://github.com/HDFGroup/hdf5_plugins> |
| `kokkos` | `5.2.2.pci` | <https://github.com/kokkos/kokkos> |
| `libtorch` | `2.14.0.pci` | <https://github.com/pytorch/pytorch> |
| `ortools` | `9.15.pci` | <https://github.com/google/or-tools> |
| `random123` | `1.14.0.pci` | <https://github.com/DEShawResearch/random123> |
| `rapidcheck` | `20260806.pci` | <https://github.com/emil-e/rapidcheck> |
| `sbva` | `20260912.pci` | <https://github.com/meelgroup/sbva> |
| `stan_math` | `5.3.0.pci` | <https://github.com/stan-dev/math> |
| `taskflow` | `4.1.0.pci` | <https://github.com/taskflow/taskflow> |
| `treedecomp` | `20260921.pci` | <https://github.com/meelgroup/treedecomp> |
| `upcxx` | `2025.10.0.pci` | <https://upcxx.lbl.gov> |
| `z3` | `5.1.0.pci` | <https://github.com/Z3Prover/z3> |
| `zpp_bits` | `4.7.6.pci` | <https://github.com/eyalz800/zpp_bits> |

Every version carries a `.pci` suffix.
It marks the recipe as packaged by this index,
and keeps it apart from a recipe of the same name and version elsewhere.
For example, conancenter ships its own `taskflow` and `zpp_bits`.

`rapidcheck`, `cadical`, `cadiback` and `treedecomp` have no upstream releases,
so each version is the date of the git revision the recipe pins.
`sbva` pins a revision after its last release, 1.2.1,
and takes the date of that revision as well.

## What each recipe packages

### clingo

The `clingo` recipe packages the C and C++ library.
Its `apps` option, off by default,
additionally builds the clingo, gringo, clasp, reify and lpconvert
executables into `bin`.
The bundled clasp and potassco are built along with it,
so the package pulls in no other recipe.

### The ganak family

`ganak` is a model counter.
It uses seven libraries, and the index packages each one as a recipe:
`cadical`, `cadiback`, `cryptominisat5`, `sbva`, `treedecomp`, `arjun` and `approxmc`.
Each recipe pins the revision that the `flake.lock` of ganak 2.7.0 names.
The revisions of `cryptominisat5`, `arjun` and `approxmc` are the release tags
that match their versions.

Every recipe in the family packages a library, static by default.
Except for `cadical` and `cadiback`,
each recipe also packages the executables that upstream installs.
The family takes `gmp`, `mpfr`, `flint` and `zlib` from conancenter.
Every recipe in it needs `compiler.cppstd=17` or later.
`cryptominisat5`, `treedecomp`, `arjun`, `approxmc` and `ganak`
need `compiler.cppstd=20` or later.

The `cryptominisat5` package also holds `liboracle`,
a second library that upstream installs with its header under `include/oracle`.
`sbva` builds against the eigen 3.4.0 that upstream vendors.
No installed header includes eigen.

The `ganak` package holds the `ganak` library and four executables:
`ganak`, `ddnnf-cleanup`, `ddnnf2dot` and `ddnnf-verify`.
Its headers sit under `include/ganak`,
so a consumer includes `<ganak/ganak.hpp>`.
`flint` 3.0.1 asks for `mpfr/4.2.1`,
and `ganak` forces `mpfr/4.2.2` to match `arjun` and `approxmc`.

### gurobi

The `gurobi` recipe packages the prebuilt linux64 distribution of Gurobi,
and supports Linux on x86_64 only.
`validate` rejects any other operating system or architecture.
The package holds the headers,
the shared library as `libgurobi130.so` and `libgurobi.so.13.0.0`,
and the C++ wrapper `libgurobi_c++.a`.

The wrapper is the one part built from source.
Its build runs the makefile that the distribution ships.
Where the profile sets `tools.build:compiler_executables`,
the makefile uses the C++ compiler named there.
The license of the package is proprietary,
and the package carries the Gurobi EULA.

### hdf5_plugins

The `hdf5_plugins` recipe packages the compression filters
that hdf5 loads at run time.
It builds twelve filters:
bitgroom, bitround, blosc, blosc2, bshuf, bzip2,
granular_bitround, jpeg, lz4, lzf, zfp and zstd.
Each one sits behind an option of its own that is on by default.
Every filter takes its compression library
from the source the release tarball bundles,
and links it in statically.
The package therefore needs no recipe other than `hdf5`.

The recipe adds its plugin directory to `HDF5_PLUGIN_PATH`,
so hdf5 finds the filters
as soon as a `VirtualRunEnv` or `VirtualBuildEnv` environment is active.

See [The linkage of the hdf5 filters](../explanation/hdf5-plugin-linkage.md).

### kokkos

The `kokkos` recipe packages the `kokkoscore`, `kokkoscontainers`,
`kokkosalgorithms` and `kokkossimd` libraries,
and the `nvcc_wrapper`, `kokkos_launch_compiler` and `hpcbind` tools.
`shared` is on by default.
Upstream always builds `kokkosalgorithms` and `kokkossimd` static,
whatever `shared` says.
`fPIC` is on by default, and applies to a static build.

The backends are `serial`, `openmp`, `threads` and `cuda`,
each behind an option of its own.
Only `serial` is on by default.
`openmp` and `threads` cannot be on together,
and at least one of `serial`, `openmp` and `threads` must be on.
The HPX, OpenACC, HIP, SYCL and NextSilicon backends are always off.

`cuda` needs `cuda_arch`, the compute capability to build for,
written as in spack, such as `80` or `89`.
Kokkos builds for one GPU architecture at a time.
The recipe does not let Kokkos detect the GPU of the build machine.
`cpu_arch` picks the host architecture,
written as the lower case suffix of the upstream `Kokkos_ARCH_<NAME>` option,
such as `zen5`, `skx` or `armv9_grace`.
`native` tunes for the build machine.
The default of both is `none`, which builds generic code.

The CUDA toolkit, OpenMP and hwloc come from the build machine,
not from conan.
`hwloc`, off by default, enables the hwloc support of Kokkos.
The recipe finds the library and header folders of hwloc through pkg-config.
Kokkos 5 has no libnuma support, so the recipe has no option for it.
Conan neither provides nor records these dependencies,
so the same ones must be present wherever the package is consumed.

`debug`, off by default, turns on the extra debug checks of Kokkos.
It does not follow `build_type`.

The profile must ask for `compiler.cppstd=20` or later.
The build needs cmake 3.22 or newer.
It takes the cmake that `tools.cmake:cmake_program` names,
or else the first one on the `PATH` of the build environment.
That `PATH` puts a cmake from `tool_requires` before the system one.
A `tool_requires` cmake older than 3.22 is rejected before anything is built.
Any other cmake is checked when the build starts, before anything is compiled.

### libtorch

The `libtorch` recipe packages the C++ API of PyTorch,
CPU only unless `with_cuda` is set.
By default, it builds `libtorch`, `libtorch_cpu` and `libc10`,
and nothing else.
There is no ROCm, XPU, MPS, Vulkan or Metal,
and no distributed support,
so gloo, tensorpipe, NCCL, MPI and UCC are all out.

`with_cuda`, off by default and Linux only,
turns on CUDA and cuDNN,
and adds `libtorch_cuda` and `libc10_cuda` to the package.
Both are taken from the build machine the way MKL is.
Conan neither provides nor records that dependency,
so the same CUDA and cuDNN must be present
wherever the package is consumed.

`with_mkldnn`, off by default,
builds the vendored oneDNN,
and routes the ATen kernels that have an oneDNN implementation through it.
Convolution and matmul are among those kernels.
The library is built from `third_party/ideep/mkl-dnn`.
PyTorch's build has no `USE_SYSTEM_MKLDNN`,
so a system oneDNN cannot be substituted
without a patch to `FindMKLDNN.cmake`.

The other optional CPU kernel libraries are off:
FBGEMM, NNPACK, QNNPACK, XNNPACK, KleidiAI and mimalloc.
Each one is a vendored source tree of its own.
Without them, the build comes to about 1560 objects.

The kineto profiler, ITT, NUMA, numpy, gflags and glog are off too.
So are the python bindings, the test binaries,
the lite interpreter and the lazy TorchScript backend.
What remains is ATen, autograd, the JIT and the C++ frontend.

BLAS, LAPACK and the FFT backend come from the MKL
installed on the build machine.
This dependency is one conan neither provides nor records.
The packaged `libtorch_cpu` carries a `DT_NEEDED` on `libmkl_intel_lp64`,
`libmkl_gnu_thread` and `libmkl_core`,
so the same MKL must be present wherever the package is consumed.
MKL here is BLAS, LAPACK and FFT only.
MKLDNN, the oneDNN kernel library, is a separate vendored tree,
and stays off unless `with_mkldnn` is set.

`eigen` is the `5.0.1` that `third_party/eigen_pin.txt` pins.
Left to itself, PyTorch git clones eigen from gitlab while it configures.

PyTorch 2.14 pins `CMAKE_CXX_STANDARD` to 20,
and `torch/all.h` and `ATen/ATen.h` refuse to be included
by anything compiling below it.
The profile must therefore ask for `compiler.cppstd=20` or later.
`validate` rejects anything lower rather than build a package
no consumer on that profile can include.

The build needs cmake 3.27 or newer,
which upstream asks for at configure time.
It also needs a python interpreter on `PATH`
with `pyyaml` and `typing_extensions` installed.
During the build, torchgen generates the ATen operator and autograd sources.
`validate_build` says so before anything is compiled.

See [The libtorch build configuration](../explanation/libtorch-build-configuration.md).

### ortools

The `ortools` recipe packages the C++ library only.
It builds the BOP, GLOP, PDLP and MathOpt solvers,
and leaves COIN-OR, GLPK, HiGHS, SCIP and CPLEX out.
The recipe does not build the flatzinc front end,
or the python, java and dotnet bindings.
The build needs cmake 3.24 or newer,
which upstream asks for at configure time.

### random123

The `random123` recipe packages the headers only.
It clones the upstream tag that matches the version,
and has no `conandata.yml`.

### rapidcheck

The `rapidcheck` recipe packages the library, static by default.
Its `enable_rtti` option is on by default.
With the option off, the package defines `RC_DONT_USE_RTTI` for consumers.
The tests and the examples are not built.

### stan_math

The `stan_math` recipe packages the headers only.
The release vendors boost 1.87.0, eigen 3.4.0, sundials 6.1.1 and tbb 2020.3
under `lib/`, and builds against those.
This recipe drops the vendored copies,
and requires `boost`, `eigen`, `sundials` and `onetbb` from conancenter instead.
All four are the newest conancenter has, except `eigen`.

`boost` is required as `header_only`.
The only compiled boost library Stan Math reaches for
is the MPI backend of `map_rect`, which is behind `STAN_MPI`.
A graph where something else needs the compiled libraries
takes them with `boost/*:header_only=False`.

See [The Stan Math dependencies](../explanation/stan-math-dependencies.md).

### taskflow

The `taskflow` recipe packages the headers only.
On Linux and FreeBSD, consumers also link `pthread`.

### upcxx

The `upcxx` recipe packages UPC++
with the GASNet-EX that its release tarball bundles.
It supports Linux, FreeBSD and macOS.
The package holds the static libraries, the headers,
and the `upcxx`, `upcxx-run`, `upcxx-meta` and `upcxx-info` tools.

The HPC libraries come from the build machine, not from conan.
These are PMIx, hwloc, rdma-core, UCX, libfabric and MPI.
The recipe finds the install prefix of PMIx and hwloc through pkg-config.
Conan neither provides nor records this dependency,
so the same libraries must be present
wherever the package is consumed.

Each GASNet-EX conduit sits behind an option of its own:
`smp`, `udp`, `ibv`, `ucx` and `ofi`.
Only `smp` is on by default.
`ibv` and `ucx` exist on Linux only.
`mpi`, off by default, adds the mpi conduit,
and builds with the `mpicxx` on `PATH`,
or with the compiler that `MPICXX` names.
A consumer of the mpi network links MPI itself.

`pmi`, on by default, makes PMIx the job spawner
of every enabled conduit that has one.
`launcher` picks the command that starts a PMIx job.
`prterun`, the default, is the launcher of PRRTE.
`srun` runs `srun --mpi=pmix` on Slurm clusters.
GASNet-EX resolves the launcher to its absolute path at build time.
`PMIRUN_CMD` in the environment overrides it at run time.
`hwloc`, on by default, enables hwloc support in GASNet-EX.
CUDA, HIP, Level Zero and PLPA are always off.

`network` picks the default network of the `upcxx` compiler wrapper.
It is also the network that conan reports to consumers.
Its default, `auto`, takes the first enabled conduit
in the order `smp`, `udp`, `ibv`, `ucx`, `ofi`, `mpi`.

UPC++ installs every code mode and thread mode in one package.
`build_type=Debug` gives a consumer the debug code mode,
and any other build type gives it the opt code mode.
The `threadmode` option picks `seq`, the default, or `par`.
Neither `build_type` nor `threadmode` changes the package id.

The package type is `static-library`,
so conan does not put the package tools on the `PATH` of a consumer by default.
A consumer that runs jobs with `upcxx-run`
declares the requirement with `run=True`.
`VirtualRunEnv` then adds `bin` to `PATH`,
and sets `UPCXX_INSTALL` to the package folder.

The package is relocatable.
The `upcxx`, `upcxx-meta` and `test-upcxx-install.sh` scripts,
the GASNet-EX `.pc` and `.mak` files, and the modulefile
find the install from their own location,
so they keep working after the package moves to another folder or cache.
A symbolic link to `upcxx` works too.
The path of the package must not contain a space,
because the upstream `upcxx` wrapper does not quote it.

### z3

The `z3` recipe packages the C and C++ library only.
The z3 executable is not built,
and neither are the python, java, dotnet, julia, ocaml and go bindings.

### zpp_bits

The `zpp_bits` recipe packages the single header `zpp_bits.h`.

## CMake targets

| Package | `find_package` | Target |
| --- | --- | --- |
| `approxmc` | `approxmc` | `approxmc` |
| `arjun` | `arjun` | `arjun` |
| `cadiback` | `cadiback` | `cadiback` |
| `cadical` | `cadical` | `cadical` |
| `clingo` | `Clingo` | `libclingo` |
| `cryptominisat5` | `cryptominisat5` | `cryptominisat5` |
| `ganak` | `ganak` | `ganak` |
| `gurobi` | `gurobi` | `gurobi::gurobi` |
| `hdf5_plugins` | `hdf5_plugins` | `hdf5_plugins::hdf5_plugins` |
| `kokkos` | `Kokkos` | `Kokkos::kokkos` |
| `libtorch` | `Torch` | `torch` |
| `ortools` | `ortools` | `ortools::ortools` |
| `random123` | `random123` | `random123::random123` |
| `rapidcheck` | `rapidcheck` | `rapidcheck` |
| `sbva` | `sbva` | `sbva` |
| `stan_math` | `stan_math` | `stan_math::stan_math` |
| `taskflow` | `Taskflow` | `Taskflow::Taskflow` |
| `treedecomp` | `treedecomp` | `treedecomp` |
| `upcxx` | `UPCXX` | `UPCXX::upcxx` |
| `z3` | `Z3` | `z3::libz3` |
| `zpp_bits` | `zpp_bits` | `zpp_bits::zpp_bits` |

A target without a namespace matches the target upstream exports.
So do the targets of `upcxx` and `kokkos`.
`gurobi`, `hdf5_plugins`, `ortools`, `random123`, `stan_math` and `zpp_bits`
use the conan defaults.

`kokkos` also offers `Kokkos::kokkoscore`, `Kokkos::kokkoscontainers`,
`Kokkos::kokkosalgorithms` and `Kokkos::kokkossimd`.
These are the package files upstream installs, not ones CMakeDeps generates,
so `kokkos_check` and the `Kokkos_DEVICES` and `Kokkos_ARCH` variables work too.
In a CUDA build, every C++ file that uses Kokkos
compiles through `nvcc_wrapper`, as upstream arranges.
`nvcc` must be on `PATH`.

The `cryptominisat5` package exports two targets,
`cryptominisat5` and `oracle`,
and the conan target `cryptominisat5::cryptominisat5` links both.

`hdf5_plugins` sets no cmake target name of its own.
With the `zfp` option on, it packages the `h5zzfp` static library
and the `zfp` codec archive that `h5zzfp` links against.
`h5zzfp` carries the property list interface of `H5Zzfp.h`.
hdf5 loads every other filter at run time,
so nothing is left to link against.
