# type: ignore
from conan import ConanFile
from conan.tools.files import get, rm
from conan.tools.layout import basic_layout
from conan.tools.gnu import AutotoolsToolchain, Autotools, PkgConfigDeps


class PrrteRecipe(ConanFile):
    name = "prrte"

    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}

    def requirements(self):
        self.requires("hwloc/2.12.2")
        self.requires("libevent/2.1.12")
        self.requires("openpmix/5.0.10.pci")

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

    def package_info(self):
        self.cpp_info.libs = ["prrte"]
