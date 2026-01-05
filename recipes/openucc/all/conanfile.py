# type: ignore
import os

from conan import ConanFile
from conan.tools.files import get, rm, rename
from conan.tools.layout import basic_layout
from conan.tools.gnu import AutotoolsToolchain, Autotools, PkgConfigDeps


class OpenUccRecipe(ConanFile):
    name = "openucc"

    # Optional metadata
    license = "BSD-3-Clause"
    author = "Parantapa Bhattacharya <pb@parantapa.net>"
    url = "https://github.com/parantapa/pb-conan-index"
    description = "UCC is a collective communication operations API and library that is flexible, complete, and feature-rich for current and emerging programming models and runtimes."

    # Binary configuration
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True],  # UCX doesn't support static
        "fPIC": [True, False],
        "rdma": [True, False],
        "cuda": [True, False],
    }
    default_options = {"shared": True, "fPIC": True, "rdma": False, "cuda": False}

    def requirements(self):
        self.requires(
            "openucx/1.20.0.pci",
            options=dict(
                rdma=self.options.get_safe("rdma"),
                cuda=self.options.get_safe("cuda"),
            ),
        )

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
        deps = PkgConfigDeps(self)
        deps.generate()

        toolchain = AutotoolsToolchain(self, prefix=self.package_folder)
        toolchain.configure_args.append("--with-valgrind=no")
        toolchain.configure_args.append("--with-mpi=no")

        toolchain.configure_args.append("--with-ucx=yes")

        if self.cuda_home is not None:
            toolchain.configure_args.append(f"--with-cuda={self.cuda_home}")
            if "NVCC_GENCODE" in os.environ:
                toolchain.configure_args.append(
                    f"--with-nvcc-gencode={os.environ['NVCC_GENCODE']}"
                )
        else:
            toolchain.configure_args.append(f"--with-cuda=no")

        toolchain.configure_args.append("--with-nvls=no")
        toolchain.configure_args.append("--with-rocm=no")
        toolchain.configure_args.append("--with-ibverbs=no")
        toolchain.configure_args.append("--with-rdmacm=no")
        toolchain.configure_args.append("--with-tls=no")
        toolchain.configure_args.append("--with-nccl=no")
        toolchain.configure_args.append("--with-rccl=no")
        toolchain.configure_args.append("--with-sharp=no")

        toolchain.configure_args.append("--with-tlcp=yes")

        toolchain.generate()

    def build(self):
        self.run("./autogen.sh", cwd=self.source_folder)
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
        self.cpp_info.libs = ["ucc"]
        self.cpp_info.set_property("pkg_config_name", "ucc")

        self.cpp_info.requires = ["openucx::openucx"]

        if self.cuda_home:
            self.cpp_info.system_libs.append("cuda")

        bin_folder = os.path.join(self.package_folder, "bin")
        self.runenv_info.prepend_path("PATH", bin_folder)
