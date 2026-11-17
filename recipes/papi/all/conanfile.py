# type: ignore
import glob
import os
import shlex

from conan import ConanFile
from conan.errors import ConanException, ConanInvalidConfiguration
from conan.tools.build import build_jobs, cross_building
from conan.tools.files import copy, get, replace_in_file, rm, rmdir
from conan.tools.gnu import AutotoolsToolchain
from conan.tools.layout import basic_layout


class PapiRecipe(ConanFile):
    name = "papi"

    description = (
        "PAPI: the Performance Application Programming Interface, "
        "a portable interface to hardware performance counters"
    )
    license = "BSD-3-Clause"
    url = "https://github.com/parantapa/pb-conan-index"
    homepage = "https://github.com/icl-utk-edu/papi"
    topics = (
        "performance",
        "performance-counters",
        "profiling",
        "hpc",
        "perf-event",
    )

    package_type = "library"
    implements = ["auto_shared_fpic"]
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {"shared": False, "fPIC": True}

    def configure(self) -> None:
        # PAPI is a C library.
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self) -> None:
        basic_layout(self, src_folder="src")

    def validate(self) -> None:
        # The perf_event component, which reads the CPU counters,
        # exists on Linux only.
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration(
                f"This recipe supports Linux only, not {self.settings.os}."
            )
        # The configure script detects the CPU and the kernel of the build machine.
        if cross_building(self):
            raise ConanInvalidConfiguration("This recipe cannot cross build PAPI.")

    def source(self) -> None:
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self) -> None:
        # The toolchain puts the compiler and the flags of the profile
        # in the environment that configure reads,
        # and -fPIC too when the fPIC option is on.
        AutotoolsToolchain(self).generate()

    @property
    def _papi_src(self) -> str:
        # The configure script and the Makefile sit in the src folder of the release.
        # They build the bundled libpfm4 in place,
        # so the build runs in the source tree.
        # Conan copies the source into the build folder of the cache,
        # so this leaves the shared source folder untouched.
        return os.path.join(self.source_folder, "src")

    def _configure_args(self) -> list[str]:
        return [
            f"--prefix={self.package_folder}",
            "--with-tests=no",
            "--disable-fortran",
            # With the static library off, configure links the utilities
            # to the shared library, with a run path into the build folder.
            # Building both kinds makes the utilities link the static library.
            # package() keeps only the library kind that the shared option picks.
            "--with-shared-lib=yes",
            "--with-static-lib=yes",
        ]

    def build(self) -> None:
        configure = shlex.join(["./configure", *self._configure_args()])
        self.run(configure, cwd=self._papi_src)

        # The shared library gets a run path to the install prefix,
        # where it finds libpfm.so.
        # $ORIGIN finds libpfm.so next to libpapi.so instead,
        # wherever the package lives.
        # make turns $$ into $, and the single quotes keep the shell off it.
        replace_in_file(
            self,
            os.path.join(self._papi_src, "Makefile"),
            '-Xlinker "-rpath" -Xlinker "$(LIBDIR)"',
            "-Xlinker \"-rpath\" -Xlinker '$$ORIGIN'",
        )

        self.run(f"make -j{build_jobs(self)}", cwd=self._papi_src)

    def package(self) -> None:
        self.run("make install", cwd=self._papi_src)

        licenses = os.path.join(self.package_folder, "licenses")
        copy(self, "LICENSE.txt", self.source_folder, licenses)
        copy(
            self,
            "COPYING",
            os.path.join(self._papi_src, "libpfm4"),
            os.path.join(licenses, "libpfm4"),
        )

        lib = os.path.join(self.package_folder, "lib")
        if self.options.shared:
            rm(self, "*.a", lib)
        else:
            rm(self, "*.so*", lib)
        # CMakeDeps and PkgConfigDeps generate what a consumer uses.
        # The upstream .pc files hold the absolute prefix.
        rmdir(self, os.path.join(lib, "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "share", "man"))

        self._check_relocatable()

    def _check_relocatable(self) -> None:
        # See "The install prefix check" in the developer notes.
        # Unlike kokkos and upcxx, it reads the binaries too,
        # so that it also catches a run path to the prefix.
        prefix = self.package_folder.encode()
        left = []
        for file in glob.glob(
            os.path.join(self.package_folder, "**", "*"), recursive=True
        ):
            if os.path.isfile(file) and not os.path.islink(file):
                with open(file, "rb") as handle:
                    if prefix in handle.read():
                        left.append(os.path.relpath(file, self.package_folder))
        if left:
            raise ConanException(
                "These files still hold the install prefix: " + ", ".join(sorted(left))
            )

    def package_info(self) -> None:
        self.cpp_info.set_property("cmake_file_name", "PAPI")
        self.cpp_info.set_property("cmake_target_name", "PAPI::PAPI")
        self.cpp_info.set_property("pkg_config_name", "papi")

        # libpapi.a and libsde.a call pthread_once and dlopen.
        # glibc before 2.34 keeps both outside libc.
        system_libs = ["pthread", "dl"]

        papi = self.cpp_info.components["libpapi"]
        papi.set_property("cmake_target_name", "PAPI::papi")
        papi.set_property("pkg_config_name", "papi-papi")
        # libpapi.a carries the objects of the bundled libpfm4.
        # libpapi.so links libpfm.so instead, and exports none of its symbols,
        # so a consumer that calls libpfm4 directly needs libpfm.so too.
        papi.libs = ["papi", "pfm"] if self.options.shared else ["papi"]
        papi.system_libs = system_libs

        # libsde lets a program export its own counters
        # as software defined events, through sde_lib.h.
        sde = self.cpp_info.components["libsde"]
        sde.set_property("cmake_target_name", "PAPI::sde")
        sde.set_property("pkg_config_name", "papi-sde")
        sde.libs = ["sde"]
        sde.system_libs = system_libs

        # bin holds papi_avail, papi_native_avail and the other utilities.
        self.cpp_info.bindirs = ["bin"]
