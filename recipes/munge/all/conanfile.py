# type: ignore
import os

from conan import ConanFile
from conan.tools.files import get, rm, rmdir, rename
from conan.tools.layout import basic_layout
from conan.tools.gnu import AutotoolsToolchain, Autotools, PkgConfigDeps


class MungeRecipe(ConanFile):
    name = "munge"

    # Optional metadata
    license = "LGPL-3.0"
    author = "Parantapa Bhattacharya <pb@parantapa.net>"
    url = "https://github.com/parantapa/pb-conan-index"
    description = "MUNGE (MUNGE Uid 'N' Gid Emporium) is an authentication service for creating and validating user credentials."

    # Binary configuration
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}

    def requirements(self):
        self.requires("openssl/3.6.0")
        self.requires("zlib/1.3.1")
        self.requires("bzip2/1.0.8")

    def source(self):
        get(self, **self.conan_data["sources"][self.version])

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def layout(self):
        basic_layout(self)

    def generate(self):
        deps = PkgConfigDeps(self)
        deps.generate()

        toolchain = AutotoolsToolchain(self, prefix=self.package_folder)
        toolchain.configure_args.append("--with-crypto-lib=openssl")
        toolchain.generate()

    def build(self):
        autotools = Autotools(self)
        autotools.configure()
        autotools.make()

    def package(self):
        autotools = Autotools(self)
        autotools.make(target="install")

        rm(self, "*.la", self.package_folder, recursive=True)
        rmdir(self, os.path.join(self.package_folder, "etc"))
        rmdir(self, os.path.join(self.package_folder, "share", "man"))
        rmdir(self, os.path.join(self.package_folder, "lib", "systemd"))
        rmdir(self, os.path.join(self.package_folder, "lib", "sysusers.d"))
        rmdir(self, os.path.join(self.package_folder, "var"))
        rename(
            self,
            os.path.join(self.package_folder, "lib", "pkgconfig"),
            os.path.join(self.package_folder, "lib", "_orig_pkgconfig"),
        )

    def package_info(self):
        self.cpp_info.libs = ["munge"]
