# type: ignore
import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMakeToolchain, CMakeDeps, CMake, cmake_layout
from conan.tools.files import copy, get, rename
from conan.tools.gnu import PkgConfigDeps


class CryptoMiniSat5Recipe(ConanFile):
    name = "cryptominisat5"

    description = "CryptoMiniSat: a SAT solver with XOR clause support"
    license = "MIT"
    url = "https://github.com/parantapa/pb-conan-index"
    homepage = "https://github.com/msoos/cryptominisat"
    topics = (
        "sat-solver",
        "sat",
        "xor",
        "solver",
        "constraint-solving",
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
        # solvertypesmini.h includes gmpxx.h.
        self.requires("gmp/6.3.0", transitive_headers=True, transitive_libs=True)
        # The cryptominisat5 executable reads gzipped CNF files through zlib.
        self.requires("zlib/1.3.2")
        self.requires("cadical/20260912.pci")
        self.requires("cadiback/20260912.pci")

    def build_requirements(self) -> None:
        self.tool_requires("pkgconf/2.5.1")

    def validate(self) -> None:
        # Upstream sets CMAKE_CXX_STANDARD to 20.
        check_min_cppstd(self, 20)

    def source(self) -> None:
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def layout(self) -> None:
        cmake_layout(self, src_folder="cryptominisat")

    def generate(self) -> None:
        CMakeDeps(self).generate()
        # Upstream finds gmp through pkg-config, not find_package.
        PkgConfigDeps(self).generate()

        tc = CMakeToolchain(self)

        # See "The meelgroup dependency lookup" in the developer notes.
        generators = self.generators_folder.replace("\\", "/")
        tc.cache_variables["cadical_DIR"] = generators
        tc.cache_variables["cadiback_DIR"] = generators
        tc.cache_variables["FETCHCONTENT_FULLY_DISCONNECTED"] = True

        # The executable links ${ZLIB_LIBRARY},
        # which the FindZLIB module sets and CMakeDeps does not.
        tc.cache_variables["ZLIB_LIBRARY"] = "ZLIB::ZLIB"

        # Upstream links the cryptominisat5 executable with -static
        # whenever the library is static.
        tc.cache_variables["STATIC_BINARY"] = False

        tc.cache_variables["ENABLE_TESTING"] = False
        tc.cache_variables["IPASIR"] = False
        tc.cache_variables["STATS"] = False
        tc.cache_variables["FINAL_PREDICTOR"] = False
        tc.cache_variables["NOBREAKID"] = True
        tc.cache_variables["NOMPI"] = True
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
        self.cpp_info.set_property("cmake_file_name", "cryptominisat5")

        solver = self.cpp_info.components["libcryptominisat5"]
        solver.libs = ["cryptominisat5"]
        solver.requires = [
            "gmp::gmp",
            "zlib::zlib",
            "cadical::cadical",
            "cadiback::cadiback",
        ]
        solver.set_property("cmake_target_name", "cryptominisat5")
        if self.settings.os in ["Linux", "FreeBSD"]:
            solver.system_libs = ["m", "pthread"]

        # oracle is a separate library that upstream installs next to the solver,
        # with its header under include/oracle.
        oracle = self.cpp_info.components["oracle"]
        oracle.libs = ["oracle"]
        oracle.set_property("cmake_target_name", "oracle")
