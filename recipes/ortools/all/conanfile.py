# type: ignore
from conan import ConanFile
from conan.tools.cmake import CMakeToolchain, CMakeDeps, CMake, cmake_layout
from conan.tools.scm import Git


class ORTools(ConanFile):
    name = "ortools"

    settings = "os", "compiler", "build_type", "arch"

    def source(self):
        git = Git(self)
        git.clone(
            url="https://github.com/google/or-tools",
            target=".",
            args=["--branch", f"v{self.version}", "--depth", "1"],
        )

    def layout(self):
        cmake_layout(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

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
        self.cpp_info.set_property("cmake_find_mode", "none")
        self.cpp_info.builddirs = [
            "lib/cmake/ZLIB",
            "lib/cmake/absl",
            "lib/cmake/bzip2",
            "lib/cmake/ortools",
            "lib/cmake/protobuf",
            "lib/cmake/re2",
            "lib/cmake/utf8_range",
        ]
