# type: ignore
import os
from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import copy, get


class Gurobi(ConanFile):
    name = "gurobi"
    version = "13.0.0"

    description = (
        "Gurobi Optimizer: a commercial solver for LP, QP, QCP, MIP, MIQP "
        "and MIQCP models"
    )
    license = "Proprietary"
    url = "https://github.com/parantapa/pb-conan-index"
    homepage = "https://www.gurobi.com"
    topics = (
        "optimization",
        "solver",
        "linear-programming",
        "mixed-integer-programming",
        "pre-built",
    )

    package_type = "shared-library"
    settings = "os", "compiler", "build_type", "arch"
    no_copy_source = True

    def validate(self):
        if self.settings.os != "Linux" or self.settings.arch != "x86_64":
            raise ConanInvalidConfiguration(
                "This recipe packages the linux64 distribution of Gurobi; "
                f"{self.settings.os}/{self.settings.arch} is not supported."
            )

    def source(self):
        get(
            self,
            "https://packages.gurobi.com/13.0/gurobi13.0.0_linux64.tar.gz",
            sha256="98455455709e8b34b34032ed90d4bf1246b14f4313a312f7c775066ff5c1f652",
            strip_root=True,
        )

    def build(self):
        copy(self, "linux64/src/*", self.source_folder, self.build_folder)
        copy(self, "linux64/include/*", self.source_folder, self.build_folder)

        compiler = self.conf.get(
            "tools.build:compiler_executables", default={}, check_type=dict
        ).get("cpp")
        args = [f'"C++={compiler}"'] if compiler else []

        self.run(
            " ".join(["make"] + args),
            cwd=os.path.join(self.build_folder, "linux64/src/build"),
        )

    def package(self):
        copy(
            self,
            "EULA.pdf",
            os.path.join(self.source_folder, "linux64"),
            os.path.join(self.package_folder, "licenses"),
        )
        copy(
            self,
            "*.txt",
            os.path.join(self.source_folder, "linux64/licenses"),
            os.path.join(self.package_folder, "licenses", "third-party"),
        )
        copy(
            self,
            "include/*.h",
            os.path.join(self.source_folder, "linux64"),
            self.package_folder,
        )
        copy(
            self,
            "libgurobi_c++.a",
            os.path.join(self.build_folder, "linux64/src/build"),
            os.path.join(self.package_folder, "lib"),
        )
        copy(
            self,
            f"libgurobi.so.{self.version}",
            os.path.join(self.source_folder, "linux64/lib"),
            os.path.join(self.package_folder, "lib"),
        )
        copy(
            self,
            f"libgurobi130.so",
            os.path.join(self.source_folder, "linux64/lib"),
            os.path.join(self.package_folder, "lib"),
        )

    def package_info(self):
        self.cpp_info.libs = ["gurobi_c++", "gurobi130"]
