# type: ignore
# fmt off
import os
from subprocess import run
from pathlib import Path

from conan import ConanFile
from conan.tools.files import get
from conan.tools.layout import basic_layout


class UPCXXRecipe(ConanFile):
    name = "upcxx"
    version = "2025.10.0"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
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

    def layout(self):
        basic_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def build(self):
        cmd = ["./configure", f"--prefix={self.package_folder}"]
        if self.options.get_safe("shared"):
            cmd.extend(["--enable-shared", "--disable-static"])
        else:
            cmd.extend(["--disable-shared", "--enable-static"])

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
                cmd.append(f"--enable-{opt}")
            else:
                cmd.append(f"--disable-{opt}")

        cmd.append("--disable-mpi-compat")
        cmd.append(f"--with-pmi-version={self.options.get_safe('pmi-version')}")

        print("Configure command:", cmd)
        run(cmd, cwd=self.source_folder, check=True)

        cmd = ["make", "all"]
        print("Make command:", cmd)
        run(cmd, cwd=self.source_folder, check=True)

    def package(self):
        Path(self.package_folder).mkdir(parents=True, exist_ok=True)

        cmd = ["make", "install"]
        print("Install command:", cmd)
        run(cmd, cwd=self.source_folder, check=True)

    def _upcxx_meta(self, codemode, threadmode, network):
        env = dict(os.environ)
        env["UPCXX_CODEMODE"] = codemode
        env["UPCXX_THREADMODE"] = threadmode
        env["UPCXX_NETWORK"] = network

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
        includedirs = [d for d in includedirs if d.startswith(self.package_folder)]

        cp = run(
            ["./bin/upcxx-meta", "LIBS"],
            env=env,
            cwd=self.package_folder,
            capture_output=True,
            check=True,
            text=True,
        )
        stdout = cp.stdout.split()
        all_libs = [x.removeprefix("-l") for x in stdout if x.startswith("-l")]
        libdirs = [x.removeprefix("-L") for x in stdout if x.startswith("-L")]

        libs = []
        system_libs = []
        for lib in all_libs:
            if lib.startswith("upcxx") or lib.startswith("gasnet"):
                libs.append(lib)
            else:
                system_libs.append(lib)

        libdirs = [d for d in libdirs if d.startswith(self.package_folder)]

        cp = run(
            ["./bin/upcxx-meta", "GASNET_PREFIX"],
            env=env,
            cwd=self.package_folder,
            capture_output=True,
            check=True,
            text=True,
        )
        gasnet_prefix = cp.stdout.strip()

        return dict(
            defines=defines,
            includedirs=includedirs,
            libs=libs,
            libdirs=libdirs,
            system_libs=system_libs,
            gasnet_prefix=gasnet_prefix,
        )

    def package_info(self):
        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.bindirs = []

        for codemode in ["opt", "debug"]:
            for threadmode in ["seq", "par"]:
                for network in ["udp", "mpi", "smp", "ucx", "ibv", "ofi"]:
                    if self.options.get_safe(network):
                        component = f"{codemode}-{threadmode}-{network}"
                        meta = self._upcxx_meta(codemode, threadmode, network)

                        self.cpp_info.components[component].defines = meta["defines"]
                        self.cpp_info.components[component].includedirs = meta[
                            "includedirs"
                        ]
                        self.cpp_info.components[component].libs = meta["libs"]
                        self.cpp_info.components[component].system_libs = meta[
                            "system_libs"
                        ]
                        self.cpp_info.components[component].libdirs = meta["libdirs"]
                        self.cpp_info.components[component].set_property(
                            "cmake_target_name", f"upcxx::{component}"
                        )

        self.runenv_info.prepend_path("PATH", os.path.join(self.package_folder, "bin"))
