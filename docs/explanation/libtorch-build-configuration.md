# The libtorch build configuration

## What the build leaves out

`with_cuda` turns on CUDA and cuDNN themselves.
The other optional CUDA libraries stay off.
cuSPARSELt backs the cuSPARSELt half of 2:4 semi-structured sparsity,
which the vendored cutlass kernels implement as well.
cuDSS backs `torch.sparse.spsolve` and nothing else.
MAGMA is a linear algebra backend
that cuSOLVER took over from and that upstream deprecated.

cuFile is off too.
So are the flash attention and memory efficient attention kernels,
and MSLK, which PyTorch turns on by itself
for a CUDA build that targets SM100a.
Each of those three vendors a source tree of its own.

## The BLAS backend

The recipe names `BLAS=MKL` explicitly rather than leave it to the default.
The explicit name makes `FindMKL` run under `find_package(MKL REQUIRED)`.
A machine without MKL then fails at configure time,
instead of falling back to eigen for BLAS.

## The source and its submodules

The source is a shallow clone of the tag rather than a release archive.
The archive ships the `third_party` folders empty,
and the repository alone records the submodule commits.
`source()` clones `v2.14.0` one commit deep,
then checks out by hand the fifteen submodules
this configuration compiles or includes against.

One of the fifteen is there for `with_mkldnn`.
ideep is the wrapper ATen includes.
It carries oneDNN itself as a submodule of its own under `mkl-dnn`,
so `source()` checks it out recursively.

Three more are there for `with_cuda`.
cutlass is on the ATen CUDA include path,
whether or not the build compiles the attention kernels that vendor it.
cudnn_frontend is the cuDNN API `torch::cudnn` includes.
NVTX carries the nvtx3 headers the CUDA build looks for,
before it falls back to the nvToolsExt library CUDA 12 no longer ships.
`source()` cannot read options,
so it fetches all four whatever those two are set to.

Four of the remaining eleven are headers only:
nlohmann, cpp-httplib, psimd and kineto.
kineto is checked out even though `USE_KINETO` is off.
`caffe2/CMakeLists.txt` puts `libkineto/include` on the `torch_cpu`
include path whether or not the flag is set,
and `kineto_shim.h` includes `ActivityType.h` from it unconditionally.
pocketfft is not among them:
it is the FFT backend for builds without MKL,
and `Dependencies.cmake` skips it once `AT_MKL_ENABLED` is set.

The remaining 22 submodules belong to the disabled features,
and `source()` never clones them.
composable_kernel, flash-attention, XNNPACK, fbgemm,
gloo and tensorpipe are among them.

`cmake/PreBuildSteps.cmake` checks that every path in `.gitmodules`
is populated before the build reads any option,
whatever that build uses.
The recipe patches that check out
rather than clone 37 submodules to satisfy it.

## Force linking `libtorch.so`

The target force links `libtorch.so` with `-Wl,--no-as-needed`.
That library is a shim with no code of its own.
The linker default of `--as-needed` therefore drops it,
and with it everything reachable only through it.
What that costs is the registration that runs from static initializers.
`torch::cuda::is_available()` answers false
on a machine with a working GPU,
once the linker drops `libtorch_cuda.so`.
Upstream force links it the same way.
