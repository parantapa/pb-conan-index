# type: ignore
import os

from conan import ConanFile
from conan.tools.files import get, rm, rename, replace_in_file
from conan.tools.layout import basic_layout
from conan.tools.gnu import AutotoolsToolchain, Autotools


class OpenUCXRecipe(ConanFile):
    name = "openucx"

    # Binary configuration
    settings = "os", "compiler", "build_type", "arch"
    options = {
        # "shared": [True, False],  # UCX doesn't support static
        "fPIC": [True, False],
        "with_verbs": [True, False],
        "with_mlx5": [True, False],
    }
    default_options = {
        # "shared": True,
        "fPIC": True,
        "with_verbs": False,
        "with_mlx5": False,
    }

    def requirements(self):
        if self.options.get_safe("with_verbs"):
            self.requires("rdma-core/61.0.pci")

    def source(self):
        get(self, **self.conan_data["sources"][self.version])

        replace_in_file(
            self,
            file_path=os.path.join(self.source_folder, "configure"),
            search='BASE_CFLAGS="-g -Wall -Werror"',
            replace='BASE_CFLAGS="-g -Wall"',
        )

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def layout(self):
        basic_layout(self)

    def generate(self):
        toolchain = AutotoolsToolchain(self)

        toolchain.configure_args.append("--disable-doxygen-doc")
        toolchain.configure_args.append("--disable-doxygen-man")
        toolchain.configure_args.append("--disable-doxygen-html")
        toolchain.configure_args.append("--disable-doxygen-pdf")

        toolchain.configure_args.append("--enable-cma")
        toolchain.configure_args.append("--enable-mt")

        toolchain.configure_args.append("--with-mpi=no")
        toolchain.configure_args.append("--with-fuse3=no")
        toolchain.configure_args.append("--with-go=no")
        toolchain.configure_args.append("--with-java=no")

        toolchain.configure_args.append("--with-mad=no")
        toolchain.configure_args.append("--with-cuda=no")
        toolchain.configure_args.append("--with-rocm=no")
        toolchain.configure_args.append("--with-ze=no")

        toolchain.configure_args.append("--with-gdrcopy=no")

        if self.options.get_safe("with_verbs"):
            rdma_dir = self.dependencies["rdma-core"].package_folder
            toolchain.configure_args.append(f"--with-verbs={rdma_dir}")

            if self.options.get_safe("with_mlx5"):
                toolchain.configure_args.append(f"--with-mlx5={rdma_dir}")
            else:
                toolchain.configure_args.append(f"--with-mlx5=no")
        else:
            toolchain.configure_args.append("--with-verbs=no")
            toolchain.configure_args.append("--with-mlx5=no")

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
        autotools.install()

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
        self.cpp_info.set_property("pkg_config_name", "ucx")

        # if self.options.get_safe("with_verbs"):
        #     self.cpp_info.requires = [
        #         "rdma-core::libibverbs",
        #         "rdma-core::libmlx5",
        #     ]
