# type: ignore
import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMakeToolchain, CMake, cmake_layout
from conan.tools.files import copy, get, rename


class SBVARecipe(ConanFile):
    name = "sbva"

    description = "SBVA: structured bounded variable addition for SAT preprocessing"
    license = "MIT"
    url = "https://github.com/parantapa/pb-conan-index"
    homepage = "https://github.com/meelgroup/sbva"
    topics = (
        "sat-solver",
        "sat",
        "preprocessing",
        "cnf",
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
        # The pinned commit comes after the last release, 1.2.1,
        # so the version is the date of the commit.
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def layout(self) -> None:
        cmake_layout(self, src_folder="sbva")

    def generate(self) -> None:
        # sbva.cpp includes the eigen 3.4.0 that upstream vendors,
        # through a private include path.
        # No installed header includes eigen, so the vendored copy stays.
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
        self.cpp_info.libs = ["sbva"]

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m", "pthread"]

        self.cpp_info.set_property("cmake_file_name", "sbva")
        self.cpp_info.set_property("cmake_target_name", "sbva")
