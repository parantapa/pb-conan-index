# type: ignore
import os

from conan import ConanFile
from conan.tools.files import copy
from conan.tools.scm import Git


class Random123(ConanFile):
    name = "random123"

    description = (
        "Counter-based random number generators: Threefry, Philox, ARS and AES"
    )
    license = "BSD-3-Clause"
    url = "https://github.com/parantapa/pb-conan-index"
    homepage = "https://github.com/DEShawResearch/random123"
    topics = ("random", "rng", "counter-based", "parallel", "header-only")

    package_type = "header-library"
    no_copy_source = True

    def source(self):
        tag = "v" + self.version.removesuffix(".pci")

        git = Git(self)
        git.clone(
            url="https://github.com/DEShawResearch/random123.git",
            target=".",
            args=["--branch", tag, "--depth", "1"],
        )

    def package(self):
        copy(
            self,
            "LICENSE",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "licenses"),
        )

        # This will also copy the "include" folder
        copy(self, "include/*.h", self.source_folder, self.package_folder)
        copy(self, "include/*.hpp", self.source_folder, self.package_folder)

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
