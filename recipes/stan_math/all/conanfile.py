# type: ignore
import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import copy, get, replace_in_file
from conan.tools.layout import basic_layout


class StanMathRecipe(ConanFile):
    name = "stan_math"

    description = "Stan Math: a C++ reverse mode automatic differentiation library"
    license = "BSD-3-Clause"
    url = "https://github.com/parantapa/pb-conan-index"
    homepage = "https://github.com/stan-dev/math"
    topics = (
        "automatic-differentiation",
        "autodiff",
        "linear-algebra",
        "probability-distributions",
        "ode-solvers",
        "header-only",
    )

    package_type = "header-library"
    implements = ["auto_header_only"]
    settings = "os", "compiler", "build_type", "arch"

    # Stan Math needs headers only from boost:
    # its math, random, numeric/odeint, lexical_cast and optional components.
    # The one place it reaches for a compiled boost library
    # is the MPI backend of map_rect,
    # which is guarded by STAN_MPI and not built by this recipe.
    default_options = {"boost/*:header_only": True}

    def requirements(self):
        # Upstream vendors boost 1.87.0, eigen 3.4.0, sundials 6.1.1
        # and tbb 2020.3 under lib/ and builds against those.
        # This recipe drops the vendored copies
        # and takes the dependencies from conancenter instead.
        self.requires("boost/1.91.0", transitive_headers=True)

        # Eigen is pinned to the 3.4 series on purpose.
        # Stan Math 5.3.0 injects its own plugin into Eigen's MatrixBase and
        # ArrayBase and reaches into Eigen internals from there,
        # and eigen 5 both fails to compile that plugin,
        # having dropped EIGEN_EMPTY_STRUCT_CTOR,
        # and crashes at run time once the plugin is made to compile.
        self.requires("eigen/3.4.1", transitive_headers=True)

        self.requires("sundials/7.5.0", transitive_headers=True, transitive_libs=True)
        self.requires("onetbb/2023.1.0", transitive_headers=True, transitive_libs=True)

    def validate(self):
        check_min_cppstd(self, 17)

    # The reverse mode solvers that wrap cvodes, idas and kinsol.
    # Every one of them holds a sundials::Context.
    _sundials_users = (
        "algebra_solver_fp.hpp",
        "cvodes_integrator.hpp",
        "cvodes_integrator_adjoint.hpp",
        "idas_service.hpp",
        "kinsol_data.hpp",
        "kinsol_solve.hpp",
    )

    def _patch_sources(self):
        # Stan Math 5.3.0 targets the sundials 6.1 headers, where
        # sundials/sundials_context.h declares both the C interface and the
        # C++ sundials::Context wrapper, and where sundials/sundials_types.h
        # still exports the pre 6.0 realtype spelling.
        # sundials 7 split the wrapper out into sundials_context.hpp
        # and moved realtype into sundials_types_deprecated.h,
        # so pulling those two headers in alongside the one Stan Math asks for
        # is enough to build against it.
        for name in self._sundials_users:
            replace_in_file(
                self,
                os.path.join(
                    self.source_folder, "stan", "math", "rev", "functor", name
                ),
                "#include <sundials/sundials_context.h>",
                "#include <sundials/sundials_context.h>\n"
                "#include <sundials/sundials_context.hpp>\n"
                "#include <sundials/sundials_types_deprecated.h>",
            )

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        self._patch_sources()

    def layout(self):
        basic_layout(self, src_folder="math")

    def package(self):
        copy(
            self,
            "LICENSE.md",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "licenses"),
        )

        # Only stan/ is packaged.
        # The lib/ folder of the release holds the vendored dependencies,
        # which the conan requirements replace.
        copy(
            self,
            "*",
            src=os.path.join(self.source_folder, "stan"),
            dst=os.path.join(self.package_folder, "include", "stan"),
        )

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []

        # init_threadpool_tbb.hpp picks its threadpool interface by including
        # tbb/tbb_stddef.h and reading TBB_VERSION_MAJOR from it.
        # oneTBB 2021 removed that header,
        # so the choice has to be made for it here.
        self.cpp_info.defines = ["TBB_INTERFACE_NEW"]

        # Both of these come from the upstream build.
        # _REENTRANT exposes the reentrant lgamma_r through cmath,
        # which Stan Math calls,
        # and BOOST_DISABLE_ASSERTS is what upstream compiles boost with.
        self.cpp_info.defines += ["_REENTRANT", "BOOST_DISABLE_ASSERTS"]

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m", "pthread"]
