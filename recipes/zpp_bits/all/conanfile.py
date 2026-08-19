# type: ignore
import os

from conan import ConanFile
from conan.tools.files import copy, get
from conan.tools.layout import basic_layout


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
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def package(self):
        copy(
            self,
            "LICENSE",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "licenses"),
        )
        copy(
            self,
            "zpp_bits.h",
            src=self.source_folder,
            dst=os.path.join(self.package_folder, "include"),
        )

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []
