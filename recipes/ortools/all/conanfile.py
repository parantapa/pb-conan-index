# type: ignore
import os

from conan import ConanFile
from conan.tools.cmake import CMakeToolchain, CMakeDeps, CMake, cmake_layout
from conan.tools.scm import Git
from conan.tools.files import rename


class ORToolsRecipe(ConanFile):
    name = "ortools"

    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {"shared": False, "fPIC": True}

    def requirements(self):
        self.requires("zlib/1.3.1", transitive_headers=True)
        self.requires("bzip2/1.0.8")
        self.requires("abseil/20250814.0", transitive_headers=True)
        self.requires("protobuf/6.32.1", transitive_headers=True)
        self.requires("eigen/5.0.1", transitive_headers=True)
        self.requires("re2/20251105")

    def build_requirements(self):
        self.tool_requires("protobuf/6.32.1")

    def source(self):
        git = Git(self)
        tag = "v" + self.version.removesuffix(".pci")
        git.clone(
            url="https://github.com/google/or-tools",
            target="or-tools",
            args=["--branch", tag, "--depth", "1"],
        )

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def layout(self):
        cmake_layout(self)

    def generate(self):
        deps = CMakeDeps(self)
        deps.generate()

        tc = CMakeToolchain(self)
        tc.variables["BUILD_DEPS"] = False
        tc.variables["USE_COINOR"] = False
        tc.variables["USE_GLPK"] = False
        tc.variables["USE_HIGHS"] = False
        tc.variables["USE_SCIP"] = False
        tc.variables["USE_CPLEX"] = False
        tc.variables["BUILD_SAMPLES"] = False
        tc.variables["BUILD_EXAMPLES"] = False
        tc.variables["BUILD_TESTING"] = False
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(
            build_script_folder=os.path.join(self.source_folder, "or-tools")
        )
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

        rename(
            self,
            os.path.join(self.package_folder, "lib", "cmake"),
            os.path.join(self.package_folder, "lib", "_orig_cmake"),
        )

    def package_info(self):
        self.cpp_info.libs = ["ortools"]
        self.cpp_info.system_libs = ["m", "dl", "pthread"]
        self.cpp_info.defines = [
            "OR_PROTO_DLL=",
            "USE_MATH_OPT",
            "USE_BOP",
            "USE_GLOP",
            "USE_PDLP",
        ]
        self.cpp_info.cflags = ["-fwrapv"]
