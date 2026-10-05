# type: ignore
import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMakeToolchain, CMakeDeps, CMake, cmake_layout
from conan.tools.files import copy, get, rename


class CadibackRecipe(ConanFile):
    name = "cadiback"

    description = "CadiBack: backbone extraction on top of CaDiCaL"
    license = "MIT"
    url = "https://github.com/parantapa/pb-conan-index"
    homepage = "https://github.com/meelgroup/cadiback"
    topics = (
        "sat-solver",
        "sat",
        "backbone",
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

    def requirements(self) -> None:
        # cadiback.h exposes no cadical type,
        # but upstream links cadical PUBLIC.
        self.requires("cadical/20260912.pci", transitive_libs=True)

    def validate(self) -> None:
        check_min_cppstd(self, 17)

    def source(self) -> None:
        # The meelgroup repository makes no releases,
        # so every version pins a commit.
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def layout(self) -> None:
        cmake_layout(self, src_folder="cadiback")

    def generate(self) -> None:
        deps = CMakeDeps(self)
        deps.generate()

        tc = CMakeToolchain(self)

        # See "The meelgroup dependency lookup" in the developer notes.
        tc.cache_variables["cadical_DIR"] = self.generators_folder.replace("\\", "/")
        tc.cache_variables["FETCHCONTENT_FULLY_DISCONNECTED"] = True

        # See "The library directory" in the developer notes.
        tc.cache_variables["CMAKE_INSTALL_LIBDIR"] = "lib"

        tc.generate()

    def build(self) -> None:
        cmake = CMake(self)
        cmake.configure()
        cmake.build(target="cadiback")

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
        self.cpp_info.libs = ["cadiback"]

        # Consumers include the header as "cadiback.h".
        self.cpp_info.includedirs = [os.path.join("include", "cadiback")]

        self.cpp_info.set_property("cmake_file_name", "cadiback")
        self.cpp_info.set_property("cmake_target_name", "cadiback")
