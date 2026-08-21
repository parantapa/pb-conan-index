# type: ignore
import os

from conan import ConanFile
from conan.tools.cmake import CMakeToolchain, CMake, cmake_layout
from conan.tools.files import copy, get, rename


class Z3Recipe(ConanFile):
    name = "z3"

    description = "Z3: an SMT solver and theorem prover from Microsoft Research"
    license = "MIT"
    url = "https://github.com/parantapa/pb-conan-index"
    homepage = "https://github.com/Z3Prover/z3"
    topics = (
        "smt",
        "solver",
        "theorem-prover",
        "constraint-solving",
        "smtlib",
    )

    package_type = "library"
    implements = ["auto_shared_fpic"]
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {"shared": False, "fPIC": True}

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def layout(self):
        cmake_layout(self, src_folder="z3")

    def generate(self):
        tc = CMakeToolchain(self)

        # This recipe packages the C and C++ library only.
        tc.variables["Z3_BUILD_LIBZ3_SHARED"] = bool(self.options.shared)
        tc.variables["Z3_BUILD_EXECUTABLE"] = False
        tc.variables["Z3_BUILD_TEST_EXECUTABLES"] = False
        tc.variables["Z3_ENABLE_EXAMPLE_TARGETS"] = False
        tc.variables["Z3_BUILD_PYTHON_BINDINGS"] = False
        tc.variables["Z3_BUILD_JAVA_BINDINGS"] = False
        tc.variables["Z3_BUILD_DOTNET_BINDINGS"] = False
        tc.variables["Z3_BUILD_JULIA_BINDINGS"] = False
        tc.variables["Z3_BUILD_OCAML_BINDINGS"] = False
        tc.variables["Z3_BUILD_GO_BINDINGS"] = False
        tc.variables["Z3_BUILD_DOCUMENTATION"] = False

        # Use the bundled multiple precision implementation
        # rather than adding a dependency on gmp.
        tc.variables["Z3_USE_LIB_GMP"] = False

        # The release tarball is not a git checkout,
        # so asking for the git hash only produces warnings.
        tc.variables["Z3_INCLUDE_GIT_HASH"] = False
        tc.variables["Z3_INCLUDE_GIT_DESCRIBE"] = False

        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(
            self,
            "LICENSE.txt",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "licenses"),
        )

        cmake = CMake(self)
        cmake.install()

        rename(
            self,
            os.path.join(self.package_folder, "lib", "cmake"),
            os.path.join(self.package_folder, "lib", "_orig_cmake"),
        )

    def package_info(self):
        self.cpp_info.libs = ["z3"]

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["pthread", "m"]

        self.cpp_info.set_property("cmake_file_name", "Z3")
        self.cpp_info.set_property("cmake_target_name", "z3::libz3")
