# type: ignore
import os

from conan import ConanFile
from conan.tools.cmake import CMakeToolchain, CMakeDeps, CMake, cmake_layout
from conan.tools.scm import Git
from conan.tools.files import rename


class ORTools(ConanFile):
    name = "ortools"

    settings = "os", "compiler", "build_type", "arch"

    def source(self):
        git = Git(self)
        git.clone(
            url="https://github.com/google/or-tools",
            target="or-tools",
            args=["--branch", f"v{self.version}", "--depth", "1"],
        )

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires("zlib/1.3.1")
        self.requires("bzip2/1.0.8")
        self.requires("abseil/20250814.0")
        self.requires("protobuf/6.32.1")
        self.requires("eigen/5.0.1")
        self.requires("re2/20251105")

    def generate(self):
        deps = CMakeDeps(self)
        deps.generate()

        tc = CMakeToolchain(self)
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
            "ZLIB::ZLIB",
            "BZip2::BZip2",
            "absl::base",
            "absl::core_headers",
            "absl::absl_check",
            "absl::absl_log",
            "absl::check",
            "absl::die_if_null",
            "absl::flags",
            "absl::flags_commandlineflag",
            "absl::flags_marshalling",
            "absl::flags_parse",
            "absl::flags_reflection",
            "absl::flags_usage",
            "absl::log",
            "absl::log_flags",
            "absl::log_globals",
            "absl::log_initialize",
            "absl::log_internal_message",
            "absl::cord",
            "absl::random_random",
            "absl::raw_hash_set",
            "absl::hash",
            "absl::leak_check",
            "absl::memory",
            "absl::meta",
            "absl::stacktrace",
            "absl::status",
            "absl::statusor",
            "absl::str_format",
            "absl::strings",
            "absl::synchronization",
            "absl::time",
            "absl::any",
            "protobuf::libprotobuf",
            "re2::re2",
            "Eigen3::Eigen",
        ]

        flatzinc = self.cpp_info.components["flatzinc"]
        flatzinc.libs = ["ortools_flatzinc"]
        flatzinc.requires = ["ortools"]
