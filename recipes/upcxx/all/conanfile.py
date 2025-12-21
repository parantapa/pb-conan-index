# type: ignore
# fmt off
import os
from subprocess import run

from conan import ConanFile
from conan.tools.files import get, replace_in_file, rmdir
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.layout import basic_layout


class UPCXXRecipe(ConanFile):
    name = "upcxx"
    version = "2025.10.0"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "cuda": [True, False],
        "hip": [True, False],
        "ze": [True, False],
        "udp": [True, False],
        "mpi": [True, False],
        "smp": [True, False],
        "ucx": [True, False],
        "ibv": [True, False],
        "ofi": [True, False],
        "pmi": [True, False],
        "pmi-version": ["x", "1", "2"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "cuda": False,
        "hip": False,
        "ze": False,
        "udp": False,
        "mpi": False,
        "smp": True,
        "ucx": False,
        "ibv": False,
        "ofi": False,
        "pmi": False,
        "pmi-version": "x",
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        basic_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        toolchain = AutotoolsToolchain(self)
        toolchain.configure_args += [
            "--disable-mpi-compat",
            f"--with-pmi-version={self.options.get_safe('pmi-version')}",
            "--enable-single=opt",
        ]

        for opt in [
            "cuda",
            "hip",
            "ze",
            "udp",
            "mpi",
            "smp",
            "ucx",
            "ibv",
            "ofi",
            "pmi",
        ]:
            if self.options.get_safe(opt):
                toolchain.configure_args.append(f"--enable-{opt}")
            else:
                toolchain.configure_args.append(f"--disable-{opt}")

        toolchain.generate()

    def build(self):
        autotools = Autotools(self)
        autotools.configure()
        autotools.make()

    def package(self):
        autotools = Autotools(self)
        autotools.install()

        rmdir(self, os.path.join(self.package_folder, "home"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        replace_in_file(
            self,
            os.path.join(self.package_folder, "bin", "upcxx-meta"),
            "//upcxx.",
            os.path.join(self.package_folder, "upcxx."),
        )

        for backend in ["udp", "mpi", "smp", "ucx", "ibv", "ofi"]:
            if self.options.get_safe(backend):
                for threadmode in ["par", "seq"]:
                    replace_in_file(
                        self,
                        os.path.join(
                            self.package_folder,
                            f"upcxx.opt.gasnet_{threadmode}.{backend}",
                            "bin",
                            "upcxx-meta",
                        ),
                        "//upcxx.",
                        os.path.join(self.package_folder, "upcxx."),
                    )
                    replace_in_file(
                        self,
                        os.path.join(
                            self.package_folder,
                            f"upcxx.opt.gasnet_{threadmode}.{backend}",
                            "bin",
                            "upcxx-meta",
                        ),
                        "//gasnet.",
                        os.path.join(self.package_folder, "gasnet."),
                    )

    def package_info(self):
        self.cpp_info.libdirs = []
        self.cpp_info.includedirs = []

        env = dict(os.environ)
        for backend in ["udp", "mpi", "smp", "ucx", "ibv", "ofi"]:
            if self.options.get_safe(backend):
                for threadmode in ["par", "seq"]:
                    env["UPCXX_THREADMODE"] = threadmode
                    env["UPCXX_NETWORK"] = backend

                    cp = run(
                        ["./bin/upcxx-meta", "CPPFLAGS"],
                        env=env,
                        cwd=self.package_folder,
                        capture_output=True,
                        check=True,
                        text=True,
                    )
                    stdout = cp.stdout.split()
                    defines = [x.removeprefix("-D") for x in stdout if x.startswith("-D")]
                    includedirs = [x.removeprefix("-I") for x in stdout if x.startswith("-I")]
                    includedirs.append(os.path.join(self.package_folder, "include"))

                    cp = run(
                        ["./bin/upcxx-meta", "LIBS"],
                        env=env,
                        cwd=self.package_folder,
                        capture_output=True,
                        check=True,
                        text=True,
                    )
                    stdout = cp.stdout.split()
                    libs = [x.removeprefix("-l") for x in stdout if x.startswith("-l")]
                    libdirs = [x.removeprefix("-L") for x in stdout if x.startswith("-L")]
                    libs.append(f"gasnet-{backend}-{threadmode}")
                    libdirs.append(os.path.join(self.package_folder, "lib"))

                    self.cpp_info.components[f"upcxx-{backend}-{threadmode}"].libs = libs
                    self.cpp_info.components[f"upcxx-{backend}-{threadmode}"].libdirs = libdirs
                    self.cpp_info.components[f"upcxx-{backend}-{threadmode}"].includedirs = includedirs
                    self.cpp_info.components[f"upcxx-{backend}-{threadmode}"].defines = defines
                    self.cpp_info.components[f"upcxx-{backend}-{threadmode}"].set_property("cmake_target_name", f"upcxx::{backend}-{threadmode}")

        self.runenv_info.define_path("GASNET_PREFIX", self.package_folder)
        self.runenv_info.prepend_path("PATH", os.path.join(self.package_folder, "bin"))
