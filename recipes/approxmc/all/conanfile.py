# type: ignore
import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMakeToolchain, CMakeDeps, CMake, cmake_layout
from conan.tools.files import copy, get, rename, replace_in_file
from conan.tools.gnu import PkgConfigDeps


class ApproxMCRecipe(ConanFile):
    name = "approxmc"

    description = "ApproxMC: an approximate model counter for CNF formulas"
    license = "MIT"
    url = "https://github.com/parantapa/pb-conan-index"
    homepage = "https://github.com/meelgroup/approxmc"
    topics = (
        "sat",
        "cnf",
        "model-counting",
        "approximate-counting",
        "hashing",
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
        # approxmc.h includes the cryptominisat5 headers.
        self.requires(
            "cryptominisat5/5.16.0.pci", transitive_headers=True, transitive_libs=True
        )
        # The approxmc executable also links gmp, mpfr and arjun.
        self.requires("arjun/2.9.0.pci")
        self.requires("gmp/6.3.0")
        self.requires("mpfr/4.2.2")
        self.requires("cadical/20260912.pci")
        self.requires("cadiback/20260912.pci")
        self.requires("zlib/1.3.2")

    def build_requirements(self) -> None:
        self.tool_requires("pkgconf/2.5.1")

    def validate(self) -> None:
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
        cmake_layout(self, src_folder="approxmc")

    def generate(self) -> None:
        CMakeDeps(self).generate()
        # Upstream finds gmp and mpfr through pkg-config, not find_package.
        PkgConfigDeps(self).generate()

        tc = CMakeToolchain(self)

        # See "The meelgroup dependency lookup" in the developer notes.
        generators = self.generators_folder.replace("\\", "/")
        for dependency in ["cadical", "cadiback", "cryptominisat5", "arjun"]:
            tc.cache_variables[f"{dependency}_DIR"] = generators
        tc.cache_variables["FETCHCONTENT_FULLY_DISCONNECTED"] = True

        # The executable links ${ZLIB_LIBRARY},
        # which the FindZLIB module sets and CMakeDeps does not.
        tc.cache_variables["ZLIB_LIBRARY"] = "ZLIB::ZLIB"

        # Upstream links the approxmc executable with -static
        # whenever the library is static.
        tc.cache_variables["STATIC_BINARY"] = False

        tc.cache_variables["USE_EVALMAXSAT"] = False
        tc.cache_variables["ENABLE_TESTING"] = False
        tc.cache_variables["BUILD_PYTHON_EXTENSION"] = False

        # A value already in the cache stops find_program,
        # and OFF keeps the manpage target out of the build.
        tc.cache_variables["HELP2MAN_FOUND"] = False

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
            "LICENSE",
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
        self.cpp_info.libs = ["approxmc"]

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m", "pthread"]

        self.cpp_info.set_property("cmake_file_name", "approxmc")
        self.cpp_info.set_property("cmake_target_name", "approxmc")
