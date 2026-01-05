# type: ignore
import os

from conan import ConanFile
from conan.tools.files import get, rm, rmdir
from conan.tools.layout import basic_layout
from conan.tools.gnu import AutotoolsToolchain, Autotools, PkgConfigDeps


class PrrteRecipe(ConanFile):
    name = "prrte"

    # Optional metadata
    license = "BSD-3-Clause"
    author = "Parantapa Bhattacharya <pb@parantapa.net>"
    url = "https://github.com/parantapa/pb-conan-index"
    description = "PMIx Reference RunTime Environment"

    # Binary configuration
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}

    def requirements(self):
        self.requires("hwloc/2.11.1")
        self.requires("libevent/2.1.12")
        self.requires("openpmix/5.0.9.pci")

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
        toolchain.configure_args.append("--with-libevent=yes")
        toolchain.configure_args.append("--with-hwloc=yes")
        toolchain.configure_args.append("--with-pmix=yes")

        toolchain.configure_args.append("--with-libev=no")
        toolchain.configure_args.append("--with-lsf=no")
        toolchain.configure_args.append("--with-slurm=no")
        toolchain.configure_args.append("--with-tm=no")
        toolchain.configure_args.append("--with-libltdl=no")
        toolchain.configure_args.append("--with-sge=no")
        toolchain.configure_args.append("--with-pbs=no")
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
        rmdir(self, os.path.join(self.package_folder, "share", "doc"))
        rmdir(self, os.path.join(self.package_folder, "share", "man"))

    def package_info(self):
        self.cpp_info.libs = ["prrte"]

        self.cpp_info.requires = [
            "hwloc::hwloc",
            "libevent::pthreads",
            "openpmix::openpmix",
        ]

        bin_folder = os.path.join(self.package_folder, "bin")
        self.runenv_info.prepend_path("PATH", bin_folder)
