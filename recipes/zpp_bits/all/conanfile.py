# type: ignore
import os

from conan import ConanFile
from conan.tools.files import copy
from conan.tools.layout import basic_layout
from conan.tools.scm import Git


class ZppBitsRecipe(ConanFile):
    name = "zpp_bits"

    description = "A lightweight C++20 binary serialization and RPC library"
    license = "MIT"
    url = "https://github.com/parantapa/pb-conan-index"
    homepage = "https://github.com/eyalz800/zpp_bits"
    topics = ("serialization", "binary", "rpc", "cpp20", "header-only")

    package_type = "header-library"
    implements = ["auto_header_only"]
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self, src_folder="zpp_bits")

    def source(self):
        tag = "v" + self.version.removesuffix(".pci")

        git = Git(self)
        git.clone(
            url="https://github.com/eyalz800/zpp_bits.git",
            target="zpp_bits",
            args=["--branch", tag, "--depth", "1"],
        )

    def package(self):
        copy(
            self,
            "LICENSE",
            src=os.path.join(self.source_folder, "zpp_bits"),
            dst=os.path.join(self.package_folder, "licenses"),
        )
        copy(
            self,
            "zpp_bits.h",
            src=os.path.join(self.source_folder, "zpp_bits"),
            dst=os.path.join(self.package_folder, "include"),
        )

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
