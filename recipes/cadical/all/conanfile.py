# type: ignore
import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMakeToolchain, CMake, cmake_layout
from conan.tools.files import copy, get, rename


class CadicalRecipe(ConanFile):
    name = "cadical"

    description = "CaDiCaL: a CDCL SAT solver, as forked by meelgroup"
    license = "MIT"
    url = "https://github.com/parantapa/pb-conan-index"
    homepage = "https://github.com/meelgroup/cadical"
    topics = (
        "sat-solver",
        "sat",
        "cdcl",
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

    def validate(self) -> None:
        check_min_cppstd(self, 17)

    def source(self) -> None:
        # The meelgroup fork makes no releases, so every version pins a commit.
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def layout(self) -> None:
        cmake_layout(self, src_folder="cadical")

    def generate(self) -> None:
        tc = CMakeToolchain(self)
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
        self.cpp_info.libs = ["cadical"]

        # Upstream installs every header flat under include/cadical,
        # and consumers include them as <cadical.hpp>.
        self.cpp_info.includedirs = [os.path.join("include", "cadical")]

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]

        self.cpp_info.set_property("cmake_file_name", "cadical")
        self.cpp_info.set_property("cmake_target_name", "cadical")
