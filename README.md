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

The `stan_math` recipe packages the headers only.
The release vendors boost 1.87.0, eigen 3.4.0, sundials 6.1.1 and tbb 2020.3
under `lib/` and builds against those;
this recipe drops the vendored copies
and requires `boost`, `eigen`, `sundials` and `onetbb` from conancenter instead.
All four are the newest conancenter has, except `eigen`.

`eigen` is held at the 3.4 series.
Stan Math injects a plugin into Eigen's `MatrixBase` and `ArrayBase`
and reaches into Eigen internals from it.
`eigen/5.0.1` does not compile that plugin,
having dropped `EIGEN_EMPTY_STRUCT_CTOR`,
and a build that defines the macro back into place segfaults at run time.

`boost` is required as `header_only`,
since the only compiled boost library Stan Math reaches for
is the MPI backend of `map_rect`, which is behind `STAN_MPI`.
Set `boost/*:header_only=False` if something else in the graph needs the
compiled libraries.

`sundials` is the current `7.5.0`,
which needs two small patches the recipe applies to the Stan Math headers.
Stan Math targets the sundials 6.1 headers,
where `sundials/sundials_context.h` declares the C++ `sundials::Context`
wrapper and `sundials/sundials_types.h` still exports `realtype`.
sundials 7 moved those into `sundials_context.hpp`
and `sundials_types_deprecated.h`,
so the recipe pulls both in alongside the header Stan Math asks for.
The cvodes, cvodes adjoint, idas and kinsol solvers were checked
against gradients and closed form solutions after the patch.

The recipe exports `TBB_INTERFACE_NEW`,
which `init_threadpool_tbb.hpp` would otherwise decide for itself
by reading `TBB_VERSION_MAJOR` out of `tbb/tbb_stddef.h`,
a header oneTBB 2021 removed.
It also exports `_REENTRANT` and `BOOST_DISABLE_ASSERTS`,
matching what the upstream makefile compiles with.
`STAN_THREADS`, `STAN_MPI` and `STAN_OPENCL` are left to the consumer;
the headers are the same either way.

The `libtorch` recipe packages the C++ API of PyTorch,
CPU only unless `with_cuda` is set.
By default it builds `libtorch`, `libtorch_cpu` and `libc10`
and nothing else:
no ROCm, XPU, MPS, Vulkan or Metal,
and no distributed support,
so gloo, tensorpipe, NCCL, MPI and UCC are all out.

`with_cuda`, off by default and Linux only,
turns on CUDA and cuDNN,
and adds `libtorch_cuda` and `libc10_cuda` to the package.
Both are taken from the build machine the way MKL is,
a system dependency conan neither provides nor records,
so the same ones have to be present wherever the package is consumed.

The other optional CUDA libraries stay off.
cuSPARSELt backs the cuSPARSELt half of 2:4 semi structured sparsity,
which the vendored cutlass kernels implement as well;
cuDSS backs `torch.sparse.spsolve` and nothing else;
and MAGMA is a linear algebra backend
that cuSOLVER has taken over from
and that upstream has deprecated.
cuFile is off too,
as are the flash attention and memory efficient attention kernels
and MSLK, which PyTorch turns on by itself
for a CUDA build that targets SM100a;
each of those three vendors a source tree of its own.

`with_mkldnn`, off by default,
builds the vendored oneDNN and routes the ATen kernels that have
an oneDNN implementation, convolution and matmul among them, through it.
The library is built from `third_party/ideep/mkl-dnn`;
there is no `USE_SYSTEM_MKLDNN` in PyTorch's build,
so a system oneDNN cannot be substituted without patching `FindMKLDNN.cmake`.

The other optional CPU kernel libraries are off:
FBGEMM, NNPACK, QNNPACK, XNNPACK, KleidiAI and mimalloc.
Each one is a vendored source tree of its own,
and together they are most of what makes a stock PyTorch build slow;
leaving them out cuts the build to about 1560 objects.
The kineto profiler, ITT, NUMA, numpy, gflags and glog are off too,
as are the python bindings, the test binaries,
the lite interpreter and the lazy TorchScript backend.
What remains is ATen, autograd, the JIT and the C++ frontend.

BLAS, LAPACK and the FFT backend come from the MKL
installed on the build machine.
`BLAS=MKL` is named explicitly rather than left to the default,
which makes `FindMKL` run under `find_package(MKL REQUIRED)`,
so a machine without MKL fails at configure time
instead of quietly falling back to eigen for BLAS.
This is a system dependency conan neither provides nor records:
the packaged `libtorch_cpu` carries a `DT_NEEDED` on `libmkl_intel_lp64`,
`libmkl_gnu_thread` and `libmkl_core`,
and the same MKL has to be present wherever the package is consumed.
Note that MKL here is BLAS, LAPACK and FFT only;
MKLDNN, the oneDNN kernel library, is a separate vendored tree
and stays off.

`eigen` is the `5.0.1` that `third_party/eigen_pin.txt` pins;
left to itself PyTorch git clones eigen from gitlab while it configures.

The source is a shallow clone of the tag rather than a release archive,
because the archive ships the `third_party` folders empty
and the submodule commits are only recorded in the repository.
`source()` clones `v2.14.0` one commit deep,
then checks out by hand the fifteen submodules
this configuration compiles or includes against.
One of the fifteen is there for `with_mkldnn`:
ideep, the wrapper ATen includes,
which carries oneDNN itself as a submodule of its own under `mkl-dnn`,
so that one is checked out recursively.
Three more are there for `with_cuda`:
cutlass, which is on the ATen CUDA include path
whether or not the attention kernels that vendor it are built,
cudnn_frontend, the cuDNN API `torch::cudnn` includes,
and NVTX, whose nvtx3 headers the CUDA build looks for
before it falls back to the nvToolsExt library CUDA 12 no longer ships.
`source()` cannot read options,
so all four are fetched whatever those two are set to.
Four of the fourteen are headers only:
nlohmann, cpp-httplib, psimd and kineto.
kineto is checked out even though `USE_KINETO` is off, because
`caffe2/CMakeLists.txt` puts `libkineto/include` on the `torch_cpu`
include path whether or not the flag is set,
and `kineto_shim.h` includes `ActivityType.h` from it unconditionally.
pocketfft is not among them:
it is the FFT backend for builds without MKL,
and `Dependencies.cmake` skips it once `AT_MKL_ENABLED` is set.
The remaining 22 submodules are the ones the disabled features would have
used, composable_kernel, flash-attention, XNNPACK, fbgemm,
gloo and tensorpipe among them, and are never cloned.

`cmake/PreBuildSteps.cmake` checks that every path in `.gitmodules`
is populated before any option is read,
whatever the build is going to use,
so the recipe patches that check out
rather than clone 37 submodules to satisfy it.

PyTorch 2.14 pins `CMAKE_CXX_STANDARD` to 20,
and `torch/all.h` and `ATen/ATen.h` refuse to be included
by anything compiling below it,
so the profile has to ask for `compiler.cppstd=20` or later.
`validate` rejects anything lower rather than build a package
no consumer on that profile could include.

Building needs a python interpreter on `PATH`
with `pyyaml` and `typing_extensions` installed;
torchgen generates the ATen operator and autograd sources during the build.
`validate_build` says so before anything is compiled.

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
`libtorch` is found as `find_package(Torch)`
and linked as `torch`, without a namespace,
matching the target upstream exports.
The target force links `libtorch.so` with `-Wl,--no-as-needed`.
That library is a shim with no code of its own,
so the linker default of `--as-needed` drops it,
and with it everything reachable only through it.
What that costs is the registration that runs from static initializers:
`torch::cuda::is_available()` answers false
on a machine with a working GPU
once `libtorch_cuda.so` has been dropped.
Upstream force links it the same way.
The other packages use the conan defaults,
so `random123` is `find_package(random123)` and `random123::random123`.

`hdf5_plugins` has no cmake target and nothing to link against.
It adds its plugin directory to `HDF5_PLUGIN_PATH` instead,
so hdf5 finds the filters
as soon as a `VirtualRunEnv` or `VirtualBuildEnv` environment is active.
