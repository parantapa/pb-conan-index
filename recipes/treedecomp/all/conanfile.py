# type: ignore
import os

from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMakeToolchain, CMake, cmake_layout
from conan.tools.files import copy, get, rename


class TreeDecompRecipe(ConanFile):
    name = "treedecomp"

    description = "TreeDecomp: tree decompositions of graphs through FlowCutter"
    license = "BSD-2-Clause"
    url = "https://github.com/parantapa/pb-conan-index"
    homepage = "https://github.com/meelgroup/treedecomp"
    topics = (
        "tree-decomposition",
        "graph",
        "treewidth",
        "flowcutter",
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
        # Upstream sets CMAKE_CXX_STANDARD to 20.
        check_min_cppstd(self, 20)

    def source(self) -> None:
        # The meelgroup repository makes no releases,
        # so every version pins a commit.
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def layout(self) -> None:
        cmake_layout(self, src_folder="treedecomp")

    def generate(self) -> None:
        tc = CMakeToolchain(self)

        # Upstream links the treedecomp executable with -static
        # whenever the library is static.
        tc.cache_variables["STATIC_BINARY"] = False

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
            "LICENSE.txt",
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
        self.cpp_info.libs = ["treedecomp"]

        if not self.options.shared:
            # Upstream exports this to consumers of the static library,
            # whose headers otherwise declare the symbols as imported on Windows.
            self.cpp_info.defines = ["TREEDECOMP_STATIC_DEFINE"]

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs = ["m"]

        self.cpp_info.set_property("cmake_file_name", "treedecomp")
        self.cpp_info.set_property("cmake_target_name", "treedecomp")
