# type: ignore
import os

from conan import ConanFile
from conan.tools.files import get, rm, rename
from conan.tools.layout import basic_layout
from conan.tools.gnu import AutotoolsToolchain, Autotools


class LibcapNgRecipe(ConanFile):
    name = "libcap-ng"

    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}

    def build_requirements(self):
        self.tool_requires("automake/1.16.5")
        self.tool_requires("libtool/2.4.7")
        self.tool_requires("pkgconf/2.5.1")

    def source(self):
        get(self, **self.conan_data["sources"][self.version])

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def layout(self):
        basic_layout(self)

    def generate(self):
        toolchain = AutotoolsToolchain(self)
        toolchain.generate()

    def build(self):
        self.run("./autogen.sh", cwd=self.source_folder)

        autotools = Autotools(self)
        autotools.configure(args=["--with-python3=no"])
        autotools.make()

    def package(self):
        autotools = Autotools(self)
        autotools.install()

        rm(self, "*.la", self.package_folder, recursive=True)

        rename(
            self,
            os.path.join(self.package_folder, "lib", "pkgconfig"),
            os.path.join(self.package_folder, "lib", "_orig_pkgconfig"),
        )

    def package_info(self):
        self.cpp_info.libs = ["cap-ng"]
        self.cpp_info.set_property("pkg_config_name", "libcap-ng")
