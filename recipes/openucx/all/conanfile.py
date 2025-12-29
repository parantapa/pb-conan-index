# type: ignore
import os

from conan import ConanFile
from conan.tools.files import get, rm, rename
from conan.tools.layout import basic_layout
from conan.tools.gnu import AutotoolsToolchain, Autotools, PkgConfigDeps


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
        "shared": [True],  # UCX doesn't support static
        "fPIC": [True, False],
        "verbs": [True, False],
    }
    default_options = {"shared": True, "fPIC": True, "verbs": False}

    def requirements(self):
        if self.options.get_safe("verbs"):
            self.requires("rdma-core/[>=52.0 <60]")

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
        toolchain.configure_args.append("--enable-cma=yes")
        toolchain.configure_args.append("--with-fuse3=no")
        toolchain.configure_args.append("--with-go=no")
        toolchain.configure_args.append("--with-java=no")
        toolchain.configure_args.append("--with-cuda=no")
        toolchain.configure_args.append("--with-rocm=no")
        toolchain.configure_args.append("--with-ze=no")
        toolchain.configure_args.append("--with-bfd=no")
        toolchain.configure_args.append("--with-gdrcopy=no")

        if self.options.get_safe("verbs"):
            toolchain.configure_args.append(f"--with-verbs=yes")
            toolchain.configure_args.append(f"--with-mlx5=yes")
        else:
            toolchain.configure_args.append(f"--with-verbs=no")
            toolchain.configure_args.append(f"--with-mlx5=no")

        toolchain.configure_args.append("--with-rdmacm=no")
        toolchain.configure_args.append("--with-doca-gpunetio=no")
        toolchain.configure_args.append("--with-efa=no")
        toolchain.configure_args.append("--with-knem=no")
        toolchain.configure_args.append("--with-xpmem=no")
        toolchain.configure_args.append("--with-ugni=no")
        toolchain.generate()

    def build(self):
        autotools = Autotools(self)
        autotools.configure()
        autotools.make()

    def package(self):
        autotools = Autotools(self)
        autotools.make(target="install")

        rm(self, "*.la", self.package_folder, recursive=True)

        rename(
            self,
            os.path.join(self.package_folder, "lib", "pkgconfig"),
            os.path.join(self.package_folder, "lib", "_orig_pkgconfig"),
        )

        rename(
            self,
            os.path.join(self.package_folder, "lib", "cmake"),
            os.path.join(self.package_folder, "lib", "_orig_cmake"),
        )

    def package_info(self):
        self.cpp_info.libs = ["ucp", "uct", "ucs", "ucm"]
