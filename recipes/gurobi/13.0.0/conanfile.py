# type: ignore
import os
from conan import ConanFile
from conan.tools.files import copy, get


class Gurobi(ConanFile):
    name = "gurobi"
    version = "13.0.0"
    no_copy_source = True

    def source(self):
        get(
            self,
            "https://packages.gurobi.com/13.0/gurobi13.0.0_linux64.tar.gz",
            strip_root=True,
        )

    def build(self):
        self.run("make", cwd=os.path.join(self.source_folder, "linux64/src/build"))

    def package(self):
        copy(
            self,
            "include/*.h",
            os.path.join(self.source_folder, "linux64"),
            self.package_folder,
        )
        copy(
            self,
            "libgurobi_c++.a",
            os.path.join(self.source_folder, "linux64/src/build"),
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
        self.cpp_info.libs = ["gurobi130", "gurobi_c++"]
