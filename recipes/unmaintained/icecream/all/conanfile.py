# type: ignore
import os

from conan import ConanFile
from conan.tools.files import get, rm, rename
from conan.tools.files.symlinks import remove_broken_symlinks
from conan.tools.layout import basic_layout
from conan.tools.gnu import AutotoolsToolchain, Autotools, PkgConfigDeps, AutotoolsDeps


class IcecreamRecipe(ConanFile):
    name = "icecream"

    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}

    def requirements(self):
        self.requires("libcap-ng/0.9.1.pci")
        self.requires(
            "libarchive/3.8.1",
            options=dict(with_acl=False, with_lzo=True, with_zstd=True),
        )
        self.requires("lzo/2.10")
        self.requires("zstd/1.5.7")

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
        deps1 = AutotoolsDeps(self)
        deps1.generate()

        deps2 = PkgConfigDeps(self)
        deps2.generate()

        toolchain = AutotoolsToolchain(self)
        toolchain.generate()

    def build(self):
        self.run("./autogen.sh", cwd=self.source_folder)

        autotools = Autotools(self)
        autotools.configure(args=["--without-man"])
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

        remove_broken_symlinks(self, self.package_folder)

    def package_info(self):
        self.cpp_info.libs = ["icecc"]
