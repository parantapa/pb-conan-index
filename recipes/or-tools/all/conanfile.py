# type: ignore
from conan import ConanFile
from conan.tools.cmake import CMakeToolchain, CMake, cmake_layout, CMakeDeps
from conan.tools.scm import Git


class ORTools(ConanFile):
    name = "or-tools"
    version = "v9.14"
    no_copy_source = True

    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}

    def source(self):
        git = Git(self)
        git.clone(
            url="https://github.com/google/or-tools",
            target=".",
            args=["--branch", self.version, "--depth", "1"],
        )

    def layout(self):
        cmake_layout(self)

    def generate(self):
        deps = CMakeDeps(self)
        deps.generate()
        tc = CMakeToolchain(self)
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(
            {
                "BUILD_DEPS": "ON",
                "USE_COINOR": "OFF",
                "USE_HIGHS": "OFF",
                "USE_SCIP": "OFF",
                "BUILD_SAMPLES": "OFF",
                "BUILD_EXAMPLES": "OFF",
                "BUILD_TESTING": "OFF",
            }
        )
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["ortools"]
