# type: ignore
from conan import ConanFile
from conan.tools.files import copy
from conan.tools.scm import Git


class Random123(ConanFile):
    name = "random123"
    version = "1.14.0"
    no_copy_source = True

    def source(self):
        git = Git(self)
        git.clone(
            url="https://github.com/DEShawResearch/random123.git",
            target=".",
            args=["--branch", f"v{self.version}", "--depth", "1"],
        )

    def package(self):
        # This will also copy the "include" folder
        copy(self, "include/*.h", self.source_folder, self.package_folder)
        copy(self, "include/*.hpp", self.source_folder, self.package_folder)

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
