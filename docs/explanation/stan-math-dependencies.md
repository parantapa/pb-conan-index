# The Stan Math dependencies

`eigen` is held at the 3.4 series.
Stan Math injects a plugin into Eigen's `MatrixBase` and `ArrayBase`
and reaches into Eigen internals from it.
`eigen/5.0.1` dropped `EIGEN_EMPTY_STRUCT_CTOR`,
so it does not compile that plugin.
A build that defines the macro back into place segfaults at run time.

`sundials` is the current `7.5.0`,
which needs two small patches the recipe applies to the Stan Math headers.
Stan Math targets the sundials 6.1 headers,
where `sundials/sundials_context.h` declares the C++ `sundials::Context`
wrapper and `sundials/sundials_types.h` still exports `realtype`.
sundials 7 moved those into `sundials_context.hpp`
and `sundials_types_deprecated.h`,
so the recipe pulls both in alongside the header Stan Math asks for.
The cvodes, cvodes adjoint, idas and kinsol solvers were checked
against gradients and closed-form solutions after the patch.

The recipe exports `TBB_INTERFACE_NEW`,
which `init_threadpool_tbb.hpp` otherwise decides for itself
by reading `TBB_VERSION_MAJOR` out of `tbb/tbb_stddef.h`,
a header oneTBB 2021 removed.
It also exports `_REENTRANT` and `BOOST_DISABLE_ASSERTS`,
which match what the upstream makefile compiles with.
`STAN_THREADS`, `STAN_MPI` and `STAN_OPENCL` are left to the consumer.
The headers are the same either way.
