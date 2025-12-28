# type: ignore
import os

from conan import ConanFile
from conan.tools.files import get
from conan.tools.layout import basic_layout
from conan.tools.gnu import PkgConfigDeps, PkgConfig


class OpenPmixRecipe(ConanFile):
    name = "openpmix"

    # Optional metadata
    license = "BSD-3-Clause"
    author = "Parantap Bhattacharya pb@parantapa.net"
    url = "https://github.com/parantapa/pb-conan-index"
    description = "PMIx Reference Library"

    # Binary configuration
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}

    def requirements(self):
        self.requires("hwloc/2.11.1")
        self.requires("libevent/2.1.12")
        self.requires("zlib/1.3.1")

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

    def build(self):
        configure_cmd = ["./configure", f"--prefix={self.package_folder}"]
        if self.options.get_safe("shared"):
            configure_cmd.extend(["--enable-shared", "--disable-static"])
        else:
            configure_cmd.extend(["--disable-shared", "--enable-static"])

        if self.options.get_safe("fPIC"):
            configure_cmd.append("--with-pic")

        configure_cmd = " ".join(configure_cmd)

        self.run(configure_cmd, cwd=self.source_folder)
        self.run(f"make", cwd=self.source_folder)

    def package(self):
        self.run(f"make install", cwd=self.source_folder)

    def package_info(self):
        pkg_config = PkgConfig(
            self,
            "pmix",
            os.path.join(self.package_folder, "lib/pkgconfig"),
        )

        pkg_config.fill_cpp_info(self.cpp_info, is_system=False, system_libs=["m"])
