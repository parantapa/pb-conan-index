# type: ignore
import os

from conan import ConanFile
from conan.tools.files import get, rmdir, rm, rename
from conan.tools.layout import basic_layout
from conan.tools.gnu import AutotoolsToolchain, Autotools, PkgConfigDeps


class OpenMPIRecipe(ConanFile):
    name = "openmpi"

    # Optional metadata
    license = "BSD-3-Clause"
    author = "Parantapa Bhattacharya <pb@parantapa.net>"
    url = "https://github.com/parantapa/pb-conan-index"
    description = "A High Performance Message Passing Library"

    # Binary configuration
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "verbs": [True, False],
        "ucx": [True, False],
    }
    default_options = {"shared": False, "fPIC": True, "verbs": False, "ucx": False}

    def requirements(self):
        self.requires("libnl/3.8.0")
        self.requires("munge/0.5.17")
        self.requires("hwloc/[>=2.11.1 <3]")
        self.requires("libevent/[>=2.1.12 <3]")
        self.requires("openpmix/5.0.9")
        self.requires("prrte/3.0.12")

        if self.options.get_safe("ucx"):
            self.requires(
                "openucx/[>=1.20.0 <2]",
                options=dict(verbs=self.options.get_safe("verbs")),
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
        toolchain.configure_args.append("--with-libnl=yes")
        toolchain.configure_args.append("--with-munge=yes")

        toolchain.configure_args.append("--with-hwloc=external")
        toolchain.configure_args.append("--with-libevent=external")
        toolchain.configure_args.append("--with-pmix=external")
        toolchain.configure_args.append(
            f"--with-prrte={self.dependencies['prrte'].package_folder}"
        )

        if self.options.get_safe("ucx"):
            toolchain.configure_args.append("--with-ucx=yes")
        else:
            toolchain.configure_args.append("--with-ucx=no")

        toolchain.configure_args.append("--with-treematch=yes")

        toolchain.configure_args.append("--enable-mpi-fortran=no")
        toolchain.configure_args.append("--enable-oshmem=no")

        toolchain.configure_args.append("--with-zlib=no")
        toolchain.configure_args.append("--with-zlibng=no")
        toolchain.configure_args.append("--with-libev=no")
        toolchain.configure_args.append("--with-lsf=no")
        toolchain.configure_args.append("--with-sge=no")
        toolchain.configure_args.append("--with-slurm=no")
        toolchain.configure_args.append("--with-tm=no")
        toolchain.configure_args.append("--with-pbs=no")
        toolchain.configure_args.append("--with-libfabric=no")
        toolchain.configure_args.append("--with-ofi=no")

        toolchain.configure_args.append("--with-cuda=no")
        toolchain.configure_args.append("--with-rocm=no")
        toolchain.configure_args.append("--with-portals4=no")
        toolchain.configure_args.append("--with-ugni=no")
        toolchain.configure_args.append("--with-libtdl=no")
        toolchain.configure_args.append("--with-valgrind=no")
        toolchain.configure_args.append("--with-memkind=no")
        toolchain.configure_args.append("--with-udreg=no")
        toolchain.configure_args.append("--with-cma=no")
        toolchain.configure_args.append("--with-knem=no")
        toolchain.configure_args.append("--with-cray-xpmem=no")
        toolchain.configure_args.append("--with-argobots=no")
        toolchain.configure_args.append("--with-qthreads=no")
        toolchain.configure_args.append("--with-hcoll=no")
        toolchain.configure_args.append("--with-ucc=no")
        toolchain.configure_args.append("--with-ime=no")
        toolchain.configure_args.append("--with-pvfs2=no")
        toolchain.configure_args.append("--with-gpfs=no")
        toolchain.configure_args.append("--with-lustre=no")
        toolchain.configure_args.append("--with-psm2=no")

        toolchain.generate()

    def build(self):
        autotools = Autotools(self)
        autotools.configure()
        autotools.make()

    def package(self):
        autotools = Autotools(self)
        autotools.make(target="install")

        rm(self, "*.la", self.package_folder, recursive=True)
        rmdir(self, os.path.join(self.package_folder, "share", "doc"))
        rmdir(self, os.path.join(self.package_folder, "share", "man"))
        rename(
            self,
            os.path.join(self.package_folder, "lib", "pkgconfig"),
            os.path.join(self.package_folder, "lib", "_orig_pkgconfig"),
        )

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.set_property("cmake_file_name", "MPI")

        self.cpp_info.components["ompi"].set_property("pkg_config_name", "ompi")
        self.cpp_info.components["ompi"].set_property("cmake_target_name", "MPI::MPI_C")
        self.cpp_info.components["ompi"].libs = ["mpi", "open-pal"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["ompi"].system_libs = ["dl", "rt"]
        self.cpp_info.components["ompi"].includedirs.append(
            os.path.join("include", "openmpi")
        )

        self.cpp_info.components["ompi"].requires = [
            "libnl::libnl",
            "munge::munge",
            "hwloc::hwloc",
            "libevent::pthreads",
            "openpmix::openpmix",
            "prrte::prrte",
        ]

        if self.options.get_safe("ucx"):
            self.cpp_info.components["ompi"].requires.append("openucx::openucx")

        bin_folder = os.path.join(self.package_folder, "bin")
        # Prepend to PATH to avoid a conflict with system MPI
        self.runenv_info.prepend_path("PATH", bin_folder)
        self.runenv_info.define_path("MPI_BIN", bin_folder)
        self.runenv_info.define_path("MPI_HOME", self.package_folder)
