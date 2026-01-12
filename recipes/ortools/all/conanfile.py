# type: ignore
import os

from conan import ConanFile
from conan.tools.cmake import CMakeToolchain, CMakeDeps, CMake, cmake_layout
from conan.tools.env import VirtualBuildEnv
from conan.tools.scm import Git
from conan.tools.files import rename


class ORToolsRecipe(ConanFile):
    name = "ortools"

    # Optional metadata
    license = "Apache 2.0"
    author = "Parantapa Bhattacharya <pb@parantapa.net>"
    url = "https://github.com/parantapa/pb-conan-index"
    description = "Google's software suite for combinatorial optimization."

    # Binary configuration
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {"shared": False, "fPIC": True}

    def requirements(self):
        self.requires("zlib/1.3.1")
        self.requires("bzip2/1.0.8")
        self.requires("abseil/20250814.0")
        self.requires("protobuf/6.32.1")
        self.requires("eigen/5.0.1")
        self.requires("re2/20251105")

    def source(self):
        git = Git(self)
        git.clone(
            url="https://github.com/google/or-tools",
            target="or-tools",
            args=["--branch", f"v{self.version}", "--depth", "1"],
        )

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def layout(self):
        cmake_layout(self)

    def generate(self):
        deps = CMakeDeps(self)
        deps.generate()

        protobuf_bin_dir = os.path.join(
            self.dependencies["protobuf"].package_folder, "bin"
        )

        buildenv = VirtualBuildEnv(self)
        buildenv.environment().prepend_path("PATH", protobuf_bin_dir)
        buildenv.generate()

        tc = CMakeToolchain(self)
        tc.presets_build_environment = buildenv.environment()
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(
            {
                "BUILD_DEPS": "OFF",
                "USE_COINOR": "OFF",
                "USE_GLPK": "OFF",
                "USE_HIGHS": "OFF",
                "USE_PDLP": "ON",
                "USE_SCIP": "OFF",
                "USE_CPLEX": "OFF",
                "BUILD_SAMPLES": "OFF",
                "BUILD_EXAMPLES": "OFF",
                "BUILD_TESTING": "OFF",
            },
            build_script_folder=os.path.join(self.source_folder, "or-tools"),
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
        self.cpp_info.system_requires = ["m", "dl", "pthreads"]
        self.cpp_info.requires = [
            "zlib::zlib",
            "bzip2::bzip2",
            "abseil::abseil",
            "protobuf::libprotobuf",
            "re2::re2",
            "eigen::eigen3",
        ]

        flatzinc = self.cpp_info.components["flatzinc"]
        flatzinc.libs = ["ortools_flatzinc", "ortools"]
        flatzinc.system_requires = self.cpp_info.system_requires
        flatzinc.requires = self.cpp_info.requires
