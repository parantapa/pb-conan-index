# Recipes

| Package | Version | Upstream |
| --- | --- | --- |
| `clingo` | `5.8.2.pci` | <https://github.com/potassco/clingo> |
| `gurobi` | `13.0.0.pci` | <https://www.gurobi.com> |
| `hdf5_plugins` | `2.2.0.pci` | <https://github.com/HDFGroup/hdf5_plugins> |
| `libtorch` | `2.14.0.pci` | <https://github.com/pytorch/pytorch> |
| `ortools` | `9.15.pci` | <https://github.com/google/or-tools> |
| `random123` | `1.14.0.pci` | <https://github.com/DEShawResearch/random123> |
| `rapidcheck` | `20260806.pci` | <https://github.com/emil-e/rapidcheck> |
| `stan_math` | `5.3.0.pci` | <https://github.com/stan-dev/math> |
| `taskflow` | `4.1.0.pci` | <https://github.com/taskflow/taskflow> |
| `z3` | `5.1.0.pci` | <https://github.com/Z3Prover/z3> |
| `zpp_bits` | `4.7.6.pci` | <https://github.com/eyalz800/zpp_bits> |

Every version carries a `.pci` suffix.
It marks the recipe as packaged by this index,
and keeps it apart from a recipe of the same name and version elsewhere.
For example, conancenter ships its own `taskflow` and `zpp_bits`.

`rapidcheck` has no upstream releases,
so its version is the date of the git revision the recipe pins.

## What each recipe packages

### clingo

The `clingo` recipe packages the C and C++ library.
Its `apps` option, off by default,
additionally builds the clingo, gringo, clasp, reify and lpconvert
executables into `bin`.
The bundled clasp and potassco are built along with it,
so the package pulls in no other recipe.

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

See [The linkage of the hdf5 filters](../explanation/hdf5-plugin-linkage.md).

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
Together they are most of what makes a stock PyTorch build slow.
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
and stays off.

`eigen` is the `5.0.1` that `third_party/eigen_pin.txt` pins.
Left to itself, PyTorch git clones eigen from gitlab while it configures.

PyTorch 2.14 pins `CMAKE_CXX_STANDARD` to 20,
and `torch/all.h` and `ATen/ATen.h` refuse to be included
by anything compiling below it.
The profile must therefore ask for `compiler.cppstd=20` or later.
`validate` rejects anything lower rather than build a package
no consumer on that profile can include.

The build needs a python interpreter on `PATH`
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
If something else in the graph needs the compiled libraries,
set `boost/*:header_only=False`.

See [The Stan Math dependencies](../explanation/stan-math-dependencies.md).

### z3

The `z3` recipe packages the C and C++ library only.
The z3 executable is not built,
and neither are the python, java, dotnet, julia, ocaml and go bindings.

## CMake targets

In CMake, `taskflow` is found as `find_package(Taskflow)`
and linked as `Taskflow::Taskflow`.
`rapidcheck` is found as `find_package(rapidcheck)`
and linked as `rapidcheck`, without a namespace,
which matches the target upstream exports.
`z3` is found as `find_package(Z3)`
and linked as `z3::libz3`.
`clingo` is found as `find_package(Clingo)`
and linked as `libclingo`, without a namespace,
which matches the target upstream exports.
`libtorch` is found as `find_package(Torch)`
and linked as `torch`, without a namespace,
which matches the target upstream exports.
The other packages use the conan defaults,
so `random123` is `find_package(random123)` and `random123::random123`.

`hdf5_plugins` sets no cmake target name of its own.
With the `zfp` option on it packages the `h5zzfp` static library,
which carries the property list interface of `H5Zzfp.h`.
hdf5 loads every other filter at run time,
so nothing is left to link against.
The recipe adds its plugin directory to `HDF5_PLUGIN_PATH` instead,
so hdf5 finds the filters
as soon as a `VirtualRunEnv` or `VirtualBuildEnv` environment is active.
