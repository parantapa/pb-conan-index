# type: ignore
import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMakeToolchain, CMakeDeps, CMake, cmake_layout
from conan.tools.files import copy, get, rename, replace_in_file
from conan.tools.gnu import PkgConfigDeps


class GanakRecipe(ConanFile):
    name = "ganak"

    description = "Ganak: an exact and probabilistic exact model counter"
    license = ("MIT", "BSD-2-Clause")
    url = "https://github.com/parantapa/pb-conan-index"
    homepage = "https://github.com/meelgroup/ganak"
    topics = (
        "sat",
        "cnf",
        "model-counting",
        "weighted-model-counting",
        "knowledge-compilation",
    )

    package_type = "library"
    implements = ["auto_shared_fpic"]
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {"shared": False, "fPIC": True}

    def requirements(self) -> None:
        # The versions of the meelgroup and msoos recipes below
        # are the commits that the flake.lock of the ganak release pins.
        # ganak.hpp includes the cryptominisat5 headers,
        # and ganak_c.h includes arjun/arjun_c.h.
        self.requires(
            "cryptominisat5/5.16.0.pci", transitive_headers=True, transitive_libs=True
        )
        self.requires("arjun/2.9.0.pci", transitive_headers=True, transitive_libs=True)
        self.requires("approxmc/4.3.4.pci", transitive_libs=True)
        self.requires("treedecomp/20260921.pci", transitive_libs=True)
        self.requires("cadical/20260912.pci")
        self.requires("cadiback/20260912.pci")
        self.requires("sbva/20260912.pci")
        # The ganak executable also links gmp, mpfr and flint.
        self.requires("gmp/6.3.0")
        # flint/3.0.1 asks for mpfr/4.2.1,
        # and arjun and approxmc for mpfr/4.2.2.
        # force settles the graph on 4.2.2.
        self.requires("mpfr/4.2.2", force=True)
        self.requires("flint/3.0.1")
        self.requires("zlib/1.3.2")

    def build_requirements(self) -> None:
        self.tool_requires("pkgconf/2.5.1")

    def validate(self) -> None:
        # Upstream sets CMAKE_CXX_STANDARD to 20.
        check_min_cppstd(self, 20)

    def source(self) -> None:
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        self._patch_sources()

    def _patch_sources(self) -> None:
        # See "The static library suffix order" in the developer notes.
        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMakeLists.txt"),
            'set(CMAKE_FIND_LIBRARY_SUFFIXES ".a" ".so" ".dylib")',
            "",
        )

    def layout(self) -> None:
        cmake_layout(self, src_folder="ganak")

    def generate(self) -> None:
        CMakeDeps(self).generate()
        # Upstream finds gmp, mpfr and flint through pkg-config,
        # not find_package.
        PkgConfigDeps(self).generate()

        tc = CMakeToolchain(self)

        # See "The meelgroup dependency lookup" in the developer notes.
        generators = self.generators_folder.replace("\\", "/")
        for dependency in [
            "cadical",
            "cadiback",
            "cryptominisat5",
            "arjun",
            "approxmc",
            "treedecomp",
        ]:
            tc.cache_variables[f"{dependency}_DIR"] = generators
        tc.cache_variables["FETCHCONTENT_FULLY_DISCONNECTED"] = True

        # The executable links ${ZLIB_LIBRARY},
        # which the FindZLIB module sets and CMakeDeps does not.
        tc.cache_variables["ZLIB_LIBRARY"] = "ZLIB::ZLIB"

        # Upstream links the ganak executable with -static
        # whenever the library is static.
        tc.cache_variables["STATIC_BINARY"] = False

        # The tests need a python interpreter with numpy.
        tc.cache_variables["ENABLE_TESTING"] = False
        tc.cache_variables["BUILD_PYTHON_EXTENSION"] = False

        # See "The library directory" in the developer notes.
        tc.cache_variables["CMAKE_INSTALL_LIBDIR"] = "lib"

        tc.generate()

    def build(self) -> None:
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self) -> None:
        copy(
            self,
            "LICENSE.txt",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "licenses"),
        )

        cmake = CMake(self)
        cmake.install()

        # See "The upstream cmake package files" in the developer notes.
        rename(
            self,
            os.path.join(self.package_folder, "lib", "cmake"),
            os.path.join(self.package_folder, "lib", "_orig_cmake"),
        )

    def package_info(self) -> None:
        self.cpp_info.libs = ["ganak"]

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m", "pthread"]

        self.cpp_info.set_property("cmake_file_name", "ganak")
        self.cpp_info.set_property("cmake_target_name", "ganak")
