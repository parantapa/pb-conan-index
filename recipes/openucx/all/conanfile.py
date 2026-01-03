# type: ignore
import os

from conan import ConanFile
from conan.tools.files import get, rm, rename
from conan.tools.layout import basic_layout
from conan.tools.gnu import AutotoolsToolchain, Autotools


class OpenUCXRecipe(ConanFile):
    name = "openucx"

    # Optional metadata
    license = "BSD-3-Clause"
    author = "Parantapa Bhattacharya <pb@parantapa.net>"
    url = "https://github.com/parantapa/pb-conan-index"
    description = "Unified Communication X (UCX) is a optimized production-proven communication framework for modern, high-bandwidth and low-latency networks."

    # Binary configuration
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True],  # UCX doesn't support static
        "fPIC": [True, False],
        "rdma": [True, False],
        "cuda": [True, False],
    }
    default_options = {"shared": True, "fPIC": True, "rdma": False, "cuda": False}

    package_id_unknown_mode = "patch_mode"

    def requirements(self):
        if self.options.get_safe("rdma"):
            self.requires("rdma-core/pci.61.0")

        self.cuda_home = None
        if self.options.get_safe("cuda"):
            for var in ["CUDA_HOME", "CUDA_PATH", "CUDA_ROOT"]:
                if var in os.environ:
                    self.cuda_home = os.environ[var]
            if self.cuda_home is None:
                raise RuntimeError(
                    "Unable to find CUDA installation; set one of CUDA_HOME/CUDA_PATH/CUDA_ROOT"
                )

    def source(self):
        get(self, **self.conan_data["sources"][self.version])

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def layout(self):
        basic_layout(self)

    def generate(self):
        toolchain = AutotoolsToolchain(self, prefix=self.package_folder)
        toolchain.configure_args.append("--enable-cma=yes")
        toolchain.configure_args.append("--with-bfd=yes")

        toolchain.configure_args.append("--with-valgrind=no")

        if self.cuda_home is not None:
            toolchain.configure_args.append(f"--with-cuda={self.cuda_home}")
        else:
            toolchain.configure_args.append(f"--with-cuda=no")

        toolchain.configure_args.append("--with-gdrcopy=no")
        toolchain.configure_args.append("--with-doca-gpunetio=no")

        toolchain.configure_args.append("--with-rocm=no")
        toolchain.configure_args.append("--with-ze=no")

        toolchain.configure_args.append("--disable-doxygen-doc")
        toolchain.configure_args.append("--disable-doxygen-man")
        toolchain.configure_args.append("--with-fuse3=no")
        toolchain.configure_args.append("--with-go=no")
        toolchain.configure_args.append("--with-java=no")

        if self.options.get_safe("rdma"):
            rdma_dir = self.dependencies["rdma-core"].package_folder

            toolchain.configure_args.append(f"--with-verbs={rdma_dir}")
            toolchain.configure_args.append("--with-rc=yes")
            toolchain.configure_args.append("--with-ud=yes")
            toolchain.configure_args.append("--with-dc=yes")
            toolchain.configure_args.append("--with-ib-hw-tm=yes")
            toolchain.configure_args.append("--with-dm=yes")
            toolchain.configure_args.append("--with-devx=yes")

            toolchain.configure_args.append(f"--with-mlx5={rdma_dir}")
        else:
            toolchain.configure_args.append("--with-verbs=no")
            toolchain.configure_args.append("--with-rc=no")
            toolchain.configure_args.append("--with-ud=no")
            toolchain.configure_args.append("--with-dc=no")
            toolchain.configure_args.append("--with-ib-hw-tm=no")
            toolchain.configure_args.append("--with-dm=no")
            toolchain.configure_args.append("--with-devx=no")

            toolchain.configure_args.append("--with-mlx5=no")

        toolchain.configure_args.append(f"--with-rdmacm=no")
        toolchain.configure_args.append("--with-mad=no")
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

        if self.options.get_safe("rdma"):
            self.cpp_info.requires = [
                "rdma-core::libibverbs",
                "rdma-core::libmlx5",
            ]

        bin_folder = os.path.join(self.package_folder, "bin")
        self.runenv_info.prepend_path("PATH", bin_folder)
