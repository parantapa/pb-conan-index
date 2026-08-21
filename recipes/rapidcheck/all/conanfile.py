# type: ignore
import os

from conan import ConanFile
from conan.tools.cmake import CMakeToolchain, CMake, cmake_layout
from conan.tools.scm import Git
from conan.tools.files import copy, rename


class RapidCheckRecipe(ConanFile):
    name = "rapidcheck"

    description = (
        "RapidCheck: a property based testing framework inspired by QuickCheck"
    )
    license = "BSD-2-Clause"
    url = "https://github.com/parantapa/pb-conan-index"
    homepage = "https://github.com/emil-e/rapidcheck"
    topics = (
        "testing",
        "property-based-testing",
        "quickcheck",
        "unit-testing",
        "fuzzing",
    )

    package_type = "library"
    implements = ["auto_shared_fpic"]
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "enable_rtti": [True, False],
    }
    default_options = {"shared": False, "fPIC": True, "enable_rtti": True}

    def source(self):
        # RapidCheck makes no releases, so every version pins a git revision.
        source = self.conan_data["sources"][self.version]

        git = Git(self)
        git.clone(url=source["url"], target="rapidcheck")
        git.folder = "rapidcheck"
        git.checkout(commit=source["commit"])

    def layout(self):
        cmake_layout(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["RC_ENABLE_RTTI"] = bool(self.options.enable_rtti)
        tc.variables["RC_ENABLE_TESTS"] = False
        tc.variables["RC_ENABLE_EXAMPLES"] = False
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(
            build_script_folder=os.path.join(self.source_folder, "rapidcheck")
        )
        cmake.build()

    def package(self):
        copy(
            self,
            "LICENSE.md",
            src=os.path.join(self.source_folder, "rapidcheck"),
            dst=os.path.join(self.package_folder, "licenses"),
        )

        cmake = CMake(self)
        cmake.install()

        rename(
            self,
            os.path.join(self.package_folder, "share", "rapidcheck", "cmake"),
            os.path.join(self.package_folder, "share", "rapidcheck", "_orig_cmake"),
        )

    def package_info(self):
        self.cpp_info.libs = ["rapidcheck"]

        if not self.options.enable_rtti:
            self.cpp_info.defines = ["RC_DONT_USE_RTTI"]

        self.cpp_info.set_property("cmake_file_name", "rapidcheck")
        self.cpp_info.set_property("cmake_target_name", "rapidcheck")
