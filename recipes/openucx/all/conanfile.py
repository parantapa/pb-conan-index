# type: ignore
import os

from conan import ConanFile
from conan.tools.files import get, rmdir
from conan.tools.layout import basic_layout
from conan.tools.gnu import AutotoolsToolchain, Autotools, PkgConfigDeps, PkgConfig


class OpenUCXRecipe(ConanFile):
    name = "openucx"

    # Optional metadata
    license = "BSD-3-Clause"
    author = "Parantapa Bhattacharya <pb@parantapa.net>"
    url = "https://github.com/parantapa/pb-conan-index"
    description = "PMIx Reference Library"

    # Binary configuration
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True],
        "fPIC": [True, False],
        "verbs": [True, False],
        "avx": [True, False],
    }
    default_options = {"shared": True, "fPIC": True, "verbs": False, "avx": True}

    def requirements(self):
        self.requires("zlib/1.3.1")
        self.requires("zstd/1.5.7")
        if self.options.get_safe("verbs"):
            self.requires("rdma-core/52.0")

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
        toolchain.configure_args.append("--disable-doxygen-doc")
        toolchain.configure_args.append("--disable-doxygen-man")

        if self.options.get_safe("avx"):
            toolchain.configure_args.append("--with-avx")

        if self.options.get_safe("verbs"):
            rdma_package_folder = self.dependencies["rdma-core"].package_folder
            toolchain.configure_args.append(f"--with-verbs={rdma_package_folder}")

        toolchain.generate()

    def build(self):
        autotools = Autotools(self)
        autotools.configure()
        autotools.make()

    def package(self):
        autotools = Autotools(self)
        autotools.make(target="install")

        rmdir(self, os.path.join(self.package_folder, "etc"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        pkg_config = PkgConfig(
            self,
            "ucx",
            os.path.join(self.package_folder, "lib/pkgconfig"),
        )

        pkg_config.fill_cpp_info(self.cpp_info, is_system=False)
