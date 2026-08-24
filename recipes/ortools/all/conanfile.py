# type: ignore
import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMakeToolchain, CMakeDeps, CMake, cmake_layout
from conan.tools.files import copy, get, rename, replace_in_file
from conan.tools.microsoft import is_msvc


class ORToolsRecipe(ConanFile):
    name = "ortools"

    description = "Google OR-Tools: a software suite for combinatorial optimization"
    license = "Apache-2.0"
    url = "https://github.com/parantapa/pb-conan-index"
    homepage = "https://developers.google.com/optimization"
    topics = (
        "optimization",
        "operations-research",
        "linear-programming",
        "constraint-programming",
        "mixed-integer-programming",
    )

    package_type = "library"
    implements = ["auto_shared_fpic"]
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    # or-tools registers its solvers through static initializers,
    # which a linker drops from a static archive because nothing refers to them.
    # A static build therefore loses GLOP and MathOpt at run time
    # unless every consumer links the whole archive,
    # so this recipe follows the upstream unix default and builds shared.
    default_options = {"shared": True, "fPIC": True}

    # The public headers re-export abseil types whose layout depends on the
    # C++ standard, so a binary built for one standard cannot serve another.
    extension_properties = {"compatibility_cppstd": False}

    def requirements(self):
        self.requires("zlib/1.3.2", transitive_headers=True, transitive_libs=True)
        self.requires("bzip2/1.0.8", transitive_libs=True)
        self.requires(
            "abseil/20260107.1", transitive_headers=True, transitive_libs=True
        )
        self.requires("protobuf/6.33.5", transitive_headers=True, transitive_libs=True)
        self.requires("eigen/5.0.1", transitive_headers=True)
        self.requires("re2/20251105", transitive_libs=True)

    def build_requirements(self):
        self.tool_requires("protobuf/6.33.5")

    def validate(self):
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def layout(self):
        cmake_layout(self, src_folder="or-tools")

    @property
    def _cppstd(self):
        # or-tools hardcodes the C++ standard, so the recipe has to know which
        # one the profile asked for. With no cppstd in the profile the compiler
        # default applies, which upstream assumes to be C++17 at the least.
        cppstd = self.settings.get_safe("compiler.cppstd")
        if cppstd is None:
            return "17"
        return str(cppstd).replace("gnu", "")

    def _patch_sources(self):
        # or-tools pins CXX_STANDARD to 17 (20 on MSVC) after project(),
        # which overrides the standard the conan toolchain sets.
        # Its abseil dependency is packaged per standard
        # and its headers only compile under the standard it was built with,
        # so leaving the pin in place breaks every profile above C++17.
        replacements = [
            (os.path.join(self.source_folder, "CMakeLists.txt"), True),
            (os.path.join(self.source_folder, "cmake", "cpp.cmake"), True),
            (
                os.path.join(
                    self.source_folder,
                    "ortools",
                    "third_party_solvers",
                    "CMakeLists.txt",
                ),
                False,
            ),
        ]
        for path, has_msvc_pin in replacements:
            replace_in_file(
                self, path, "CXX_STANDARD 17", f"CXX_STANDARD {self._cppstd}"
            )
            if has_msvc_pin:
                replace_in_file(
                    self, path, "CXX_STANDARD 20", f"CXX_STANDARD {self._cppstd}"
                )

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

        # The flatzinc front end is a MiniZinc command line tool,
        # not part of the library this recipe packages.
        # It also pins its own C++ standard, which _patch_sources does not fix
        # so building it would fail against a C++20 abseil.
        tc.variables["BUILD_FLATZINC"] = False

        # GNUInstallDirs picks lib64 on 64 bit non-Debian Linux,
        # which would put the library outside the directories
        # this recipe reports to consumers.
        tc.cache_variables["CMAKE_INSTALL_LIBDIR"] = "lib"

        tc.generate()

    def build(self):
        self._patch_sources()

        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(
            self,
            "LICENSE",
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
        self.cpp_info.libs = ["ortools"]

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m", "dl", "pthread"]

        self.cpp_info.defines = [
            "OR_PROTO_DLL=",
            "USE_MATH_OPT",
            "USE_BOP",
            "USE_GLOP",
            "USE_PDLP",
        ]

        # or-tools compiles itself with -fwrapv and exports it to consumers,
        # since its inline code relies on signed overflow wrapping.
        # The -Wno-range-loop-construct and -Wno-sign-compare that upstream
        # exports alongside it are left out on purpose;
        # they would silence those warnings in consumer code too.
        if not is_msvc(self):
            self.cpp_info.cxxflags = ["-fwrapv"]
