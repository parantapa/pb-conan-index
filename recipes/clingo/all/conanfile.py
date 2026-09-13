# type: ignore
import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMakeToolchain, CMake, cmake_layout
from conan.tools.files import copy, get, rename, rm


class ClingoRecipe(ConanFile):
    name = "clingo"

    description = "Clingo: an answer set programming grounder and solver"
    license = "MIT"
    url = "https://github.com/parantapa/pb-conan-index"
    homepage = "https://potassco.org/clingo"
    topics = (
        "answer-set-programming",
        "logic-programming",
        "solver",
        "grounder",
        "constraint-solving",
    )

    package_type = "library"
    implements = ["auto_shared_fpic"]
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "apps": [True, False],
    }
    default_options = {"shared": False, "fPIC": True, "apps": False}

    def validate(self):
        check_min_cppstd(self, 14)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def layout(self):
        cmake_layout(self, src_folder="clingo")

    def generate(self):
        tc = CMakeToolchain(self)

        tc.variables["CLINGO_BUILD_APPS"] = bool(self.options.apps)
        tc.variables["CLINGO_BUILD_TESTS"] = False
        tc.variables["CLINGO_BUILD_EXAMPLES"] = False
        tc.variables["CLINGO_BUILD_WEB"] = False

        tc.cache_variables["CLINGO_BUILD_WITH_PYTHON"] = "OFF"
        tc.cache_variables["CLINGO_BUILD_WITH_LUA"] = "OFF"

        # CLINGO_BUILD_STATIC also turns off position independent code,
        # so a static build goes through CLINGO_BUILD_SHARED instead
        # and leaves fPIC to conan.
        tc.variables["CLINGO_BUILD_STATIC"] = False
        tc.variables["CLINGO_BUILD_SHARED"] = bool(self.options.shared)

        # clingo hides all symbols when it builds a shared libclingo and
        # expects the bundled clasp and potassco to be static and absorbed
        # into it. With BUILD_SHARED_LIBS on, those become shared libraries
        # too, and libclingo keeps unresolved clasp symbols.
        tc.cache_variables["BUILD_SHARED_LIBS"] = False

        tc.variables["CLINGO_INSTALL_LIB"] = True

        tc.variables["CLASP_INSTALL_LIB"] = True
        tc.variables["LIB_POTASSCO_INSTALL_LIB"] = True

        # Conan manages the rpath of the packaged libraries.
        tc.variables["CLINGO_MANAGE_RPATH"] = False

        tc.cache_variables["CMAKE_DISABLE_FIND_PACKAGE_BISON"] = True
        tc.cache_variables["CMAKE_DISABLE_FIND_PACKAGE_RE2C"] = True

        tc.cache_variables["CMAKE_INSTALL_LIBDIR"] = "lib"

        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(
            self,
            "LICENSE.md",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "licenses"),
        )
        copy(
            self,
            "LICENSE",
            src=os.path.join(self.source_folder, "clasp"),
            dst=os.path.join(self.package_folder, "licenses", "clasp"),
        )

        cmake = CMake(self)
        cmake.install()

        rename(
            self,
            os.path.join(self.package_folder, "lib", "cmake"),
            os.path.join(self.package_folder, "lib", "_orig_cmake"),
        )

        if self.options.shared:
            # clasp and potassco are exported only so that cmake can
            # generate the config clingo installs.
            # A shared libclingo already contains them.
            rm(self, "*.a", os.path.join(self.package_folder, "lib"))

    def package_info(self):
        if self.options.shared:
            self.cpp_info.libs = ["clingo"]
        else:
            # A static build keeps the bundled grounder and solver
            # in libraries of their own, so a consumer links them as well.
            # The order follows the upstream link interface:
            # clingo needs gringo and clasp,
            # gringo needs reify and potassco, and clasp needs potassco.
            self.cpp_info.libs = [
                "clingo",
                "gringo",
                "clasp",
                "reify",
                "potassco",
            ]

            # Upstream exports this to consumers of the static library,
            # whose headers otherwise declare the symbols as imported.
            self.cpp_info.defines = ["CLINGO_NO_VISIBILITY"]

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m", "pthread"]

        self.cpp_info.set_property("cmake_file_name", "Clingo")
        self.cpp_info.set_property("cmake_target_name", "libclingo")
