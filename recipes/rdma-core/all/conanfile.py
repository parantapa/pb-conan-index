# type: ignore
import os

from conan import ConanFile
from conan.tools.files import get, patch, rmdir, rename, replace_in_file
from conan.tools.gnu import PkgConfigDeps
from conan.tools.cmake import CMakeToolchain, CMake, cmake_layout


class RdmaCoreRecipe(ConanFile):
    name = "rdma-core"

    # Optional metadata
    license = ("GPL-2.0", "Linux-OpenIB", "BSD-2-Clause")
    author = "Parantapa Bhattacharya <pb@parantapa.net>"
    url = "https://github.com/parantapa/pb-conan-index"
    description = "RDMA core userspace libraries."

    # Binary configuration
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True], "fPIC": [True, False]}
    default_options = {"shared": True, "fPIC": True}

    exports_sources = "patches/*"

    def source(self):
        get(self, **self.conan_data["sources"][self.version])

        for it in self.conan_data["patches"][self.version]:
            patch(self, strip=1, **it)

        cmakelists_path = os.path.join(self.source_folder, "CMakeLists.txt")
        replace_in_file(self, cmakelists_path, "libnl-3.0 libnl-route-3.0", "libnl")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires("libnl/3.9.0")

    def validate(self):
        if self.settings.os not in ["Linux", "FreeBSD"]:
            # libnl is only available on Linux
            raise ConanInvalidConfiguration("rdma-core is only supported on Linux")

    def generate(self):
        deps = PkgConfigDeps(self)
        deps.generate()

        toolchain = CMakeToolchain(self)
        toolchain.variables["IN_PLACE"] = False
        toolchain.variables["ENABLE_VALGRIND"] = False
        toolchain.variables["NO_PYVERBS"] = True
        toolchain.variables["NO_MAN_PAGES"] = True
        toolchain.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

        rmdir(self, os.path.join(self.package_folder, "share", "doc"))
        rename(
            self,
            os.path.join(self.package_folder, "lib", "pkgconfig"),
            os.path.join(self.package_folder, "lib", "_orig_pkgconfig"),
        )

    def package_info(self):
        def _add_component(name, requires, pthread=False):
            component = self.cpp_info.components[name]
            component.set_property("pkg_config_name", name)
            component.libs = [name.replace("lib", "")]
            component.requires = requires
            if pthread and self.settings.os in ["Linux", "FreeBSD"]:
                component.system_libs = ["pthread"]

        _add_component("libibmad", ["libibumad"])
        _add_component("libibnetdisc", ["libibmad", "libibumad"])
        _add_component("libibumad", [])
        _add_component("libibverbs", ["libnl::nl", "libnl::nl-route"], pthread=True)
        _add_component("libmlx5", ["libibverbs"], pthread=True)
        _add_component(
            "librdmacm", ["libibverbs", "libnl::nl", "libnl::nl-route"], pthread=True
        )

        bin_folder = os.path.join(self.package_folder, "bin")
        self.runenv_info.prepend_path("PATH", bin_folder)
