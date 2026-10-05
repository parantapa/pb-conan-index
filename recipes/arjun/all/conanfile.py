# type: ignore
import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMakeToolchain, CMakeDeps, CMake, cmake_layout
from conan.tools.files import copy, get, rename, replace_in_file
from conan.tools.gnu import PkgConfigDeps


class ArjunRecipe(ConanFile):
    name = "arjun"

    description = "Arjun: a CNF minimizer and independent support calculator"
    license = "MIT"
    url = "https://github.com/parantapa/pb-conan-index"
    homepage = "https://github.com/meelgroup/arjun"
    topics = (
        "sat",
        "cnf",
        "preprocessing",
        "model-counting",
        "independent-support",
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
        # arjun.h includes gmpxx.h, mpfr.h and the cryptominisat5 headers.
        self.requires("gmp/6.3.0", transitive_headers=True, transitive_libs=True)
        self.requires("mpfr/4.2.2", transitive_headers=True, transitive_libs=True)
        self.requires(
            "cryptominisat5/5.16.0.pci", transitive_headers=True, transitive_libs=True
        )
        self.requires("sbva/20260912.pci", transitive_libs=True)
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
        cmake_layout(self, src_folder="arjun")

    def generate(self) -> None:
        CMakeDeps(self).generate()
        # Upstream finds gmp and mpfr through pkg-config, not find_package.
        PkgConfigDeps(self).generate()

        tc = CMakeToolchain(self)

        # See "The meelgroup dependency lookup" in the developer notes.
        generators = self.generators_folder.replace("\\", "/")
        for dependency in ["cadical", "cadiback", "cryptominisat5", "sbva"]:
            tc.cache_variables[f"{dependency}_DIR"] = generators
        tc.cache_variables["FETCHCONTENT_FULLY_DISCONNECTED"] = True

        # The executables link ${ZLIB_LIBRARY},
        # which the FindZLIB module sets and CMakeDeps does not.
        tc.cache_variables["ZLIB_LIBRARY"] = "ZLIB::ZLIB"

        # Upstream links the arjun executable with -static
        # whenever the library is static.
        tc.cache_variables["STATIC_BINARY"] = False

        # EXTRA_SYNTH needs mlpack, armadillo, ensmallen and EvalMaxSAT.
        tc.cache_variables["EXTRA_SYNTH"] = False
        tc.cache_variables["ENABLE_TESTING"] = False

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
        self.cpp_info.libs = ["arjun"]

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m", "pthread"]

        self.cpp_info.set_property("cmake_file_name", "arjun")
        self.cpp_info.set_property("cmake_target_name", "arjun")
