# type: ignore
import os

from conan import ConanFile
from conan.tools.files import get, rm, rmdir, rename
from conan.tools.layout import basic_layout
from conan.tools.gnu import AutotoolsToolchain, Autotools, PkgConfigDeps


class OpenPmixRecipe(ConanFile):
    name = "openpmix"

    # Optional metadata
    license = "BSD-3-Clause"
    author = "Parantapa Bhattacharya <pb@parantapa.net>"
    url = "https://github.com/parantapa/pb-conan-index"
    description = "PMIx Reference Library"

    # Binary configuration
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}

    def requirements(self):
        self.requires("hwloc/[>=2.11.1 <3]")
        self.requires("libevent/[>=2.1.12 <3]")
        self.requires("zlib/[>=1.3.1 <2]")
        self.requires("zlib-ng/[>=2.3.2 <3]")
        self.requires("munge/0.5.17")

    def source(self):
        get(self, **self.conan_data["sources"][self.version])

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def layout(self):
        basic_layout(self)

    def generate(self):
        deps = PkgConfigDeps(self)
        deps.set_property("zlib-ng", "pkg_config_name", "zlibng")
        deps.generate()

        toolchain = AutotoolsToolchain(self, prefix=self.package_folder)
        toolchain.configure_args.append("--with-hwloc=yes")
        toolchain.configure_args.append("--with-libevent=yes")
        toolchain.configure_args.append("--with-zlib=yes")
        toolchain.configure_args.append("--with-zlibng=yes")
        toolchain.configure_args.append("--with-munge=yes")

        toolchain.configure_args.append("--enable-python-bindings=no")
        toolchain.configure_args.append("--with-libev=no")
        toolchain.configure_args.append("--with-libltdl=no")
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
        rename(
            self,
            os.path.join(self.package_folder, "lib", "pkgconfig"),
            os.path.join(self.package_folder, "lib", "_orig_pkgconfig"),
        )

    def package_info(self):
        self.cpp_info.libs = ["pmix"]
        self.cpp_info.includedirs.append(os.path.join("include", "pmix"))
        self.cpp_info.system_libs.extend(["dl", "m", "util"])

        self.cpp_info.requires = [
            "hwloc::hwloc",
            "libevent::pthreads",
            "zlib::zlib",
            "zlib-ng::zlib-ng",
            "munge::munge",
        ]

        self.cpp_info.set_property("pkg_config_name", "pmix")

        bin_folder = os.path.join(self.package_folder, "bin")
        self.runenv_info.prepend_path("PATH", bin_folder)
