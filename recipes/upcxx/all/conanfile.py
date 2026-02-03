# type: ignore
import os
import io
import shlex

from conan import ConanFile
from conan.tools.files import get, rm, rename
from conan.tools.layout import basic_layout
from conan.tools.gnu import AutotoolsToolchain, Autotools, PkgConfigDeps


class UpcxxRecipe(ConanFile):
    name = "upcxx"

    # Binary configuration
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [False],
        "fPIC": [True, False],
        "rdma": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "rdma": False,
    }

    def requirements(self):
        self.requires("hwloc/2.12.2")
        self.requires("openpmix/5.0.10.pci")
        if self.options.get_safe("rdma"):
            self.requires("rdma-core/61.0.pci")

    def source(self):
        get(self, **self.conan_data["sources"][self.version]["upcxx"])
        get(self, **self.conan_data["sources"][self.version]["gasnet"])

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def layout(self):
        basic_layout(self)

    def generate(self):
        deps = PkgConfigDeps(self)
        deps.generate()

        toolchain = AutotoolsToolchain(self, prefix=self.package_folder)
        toolchain.generate()

    def _get_cflags(self, pc):
        with io.StringIO() as fobj:
            self.run(f"pkg-config --cflags {pc}", stdout=fobj)
            cflags = fobj.getvalue().strip()
            return shlex.join(shlex.split(cflags))

    def _get_libs(self, pc):
        with io.StringIO() as fobj:
            self.run(f"pkg-config --libs {pc}", stdout=fobj)
            libs = fobj.getvalue().strip()
            return shlex.join(shlex.split(libs))

    def build(self):
        configure_args = []

        configure_args.append("--disable-cuda")
        configure_args.append("--disable-hip")
        configure_args.append("--disable-ze")

        gasnet_source = os.path.join(self.source_folder, "gasnet")
        configure_args.append(f"--with-gasnet={gasnet_source}")

        configure_args.append("--disable-udp")
        configure_args.append("--disable-mpi-compat")
        configure_args.append("--disable-mpi")
        configure_args.append("--disable-ucx")
        configure_args.append("--disable-ofi")

        configure_args.append("--enable-smp")
        configure_args.append("--with-smp-spawner=pmi")

        if self.options.get_safe("rdma"):
            ibv_home = self.dependencies["rdma-core"].package_folder
            ibv_cflags = self._get_cflags("libmlx5")
            ibv_libs = self._get_libs("libmlx5")

            configure_args.append("--enable-ibv")
            configure_args.append(f"--with-ibv-home={ibv_home}")
            configure_args.append(f"--with-ibv-cflags={ibv_cflags}")
            configure_args.append(f"--with-ibv-libs={ibv_libs}")
            configure_args.append("--with-ibv-spawner=pmi")
        else:
            configure_args.append("--disable-ibv")

        pmix_home = self.dependencies["openpmix"].package_folder
        pmix_libs = self._get_libs("pmix")

        configure_args.append("--enable-pmi")
        configure_args.append("--with-pmi-version=x")
        configure_args.append(f"--with-pmi-home={pmix_home}")
        configure_args.append(f"--with-pmi-libs={pmix_libs}")
        configure_args.append('--with-pmirun-cmd="prterun -n %N %P %Q"')

        configure_args.append("--disable-plpa")

        hwloc_home = self.dependencies["hwloc"].package_folder
        hwloc_cflags = self._get_cflags("hwloc")
        hwloc_libs = self._get_libs("hwloc")

        configure_args.append("--enable-hwloc")
        configure_args.append(f"--with-hwloc-home={hwloc_home}")
        configure_args.append(f"--with-hwloc-cflags={hwloc_cflags}")
        configure_args.append(f"--with-hwloc-libs={hwloc_libs}")

        configure_args.append("--enable-single=opt")

        autotools = Autotools(self)
        autotools.configure(build_script_folder="upcxx", args=configure_args)
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
            os.path.join(self.package_folder, "share", "cmake"),
            os.path.join(self.package_folder, "share", "_orig_cmake"),
        )

    def package_info(self):
        networks = ["smp"]
        threadmodes = ["seq", "par"]
        codemodes = ["opt"]

        if self.options.get_safe("rdma"):
            networks.append("ibv")

        for net in networks:
            for tmode in threadmodes:
                comp = self.cpp_info.components[f"gasnet-{net}-{tmode}"]

                comp.defines.append("_GNU_SOURCE=1")
                comp.defines.append(f"GASNET_{tmode.upper()}")

                if not (net == "smp" and tmode == "seq"):
                    comp.defines.append(f"_REENTRANT")

                comp.includedirs.append(os.path.join("include", f"{net}-conduit"))
                comp.libs = [f"gasnet-{net}-{tmode}"]
                comp.requires.append("openpmix::openpmix")
                comp.requires.append("hwloc::hwloc")
                if net == "ibv":
                    comp.requires.append("rdma-core::libibverbs")
                    comp.requires.append("rdma-core::libmlx5")

        for net in networks:
            for tmode in threadmodes:
                for cmode in codemodes:
                    comp = self.cpp_info.components[f"{net}-{tmode}-{cmode}"]

                    comp.defines.append("UPCXXI_ASSERT_ENABLED=0")
                    comp.defines.append("UPCXXI_BACKEND=1")
                    comp.defines.append(f"UPCXXI_BACKEND_GASNET_{tmode.upper()}=1")

                    comp.includedirs.append(
                        os.path.join(
                            self.package_folder,
                            f"upcxx.{cmode}.gasnet_{tmode}.{net}",
                            "gen_include",
                        )
                    )

                    comp.libs = ["upcxx"]
                    comp.libdirs.append(
                        os.path.join(
                            self.package_folder,
                            f"upcxx.{cmode}.gasnet_{tmode}.{net}",
                            "lib",
                        )
                    )

                    comp.requires.append(f"gasnet-{net}-{tmode}")
