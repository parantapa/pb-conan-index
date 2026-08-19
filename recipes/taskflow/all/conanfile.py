# type: ignore
import os

from conan import ConanFile
from conan.tools.files import copy, get
from conan.tools.layout import basic_layout


class TaskflowRecipe(ConanFile):
    name = "taskflow"

    description = "A general-purpose parallel and heterogeneous task programming system"
    license = "MIT"
    url = "https://github.com/parantapa/pb-conan-index"
    homepage = "https://taskflow.github.io"
    topics = (
        "parallel",
        "task-parallelism",
        "concurrency",
        "threadpool",
        "header-only",
    )

    package_type = "header-library"
    implements = ["auto_header_only"]
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self, src_folder="taskflow")

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
            "*",
            src=os.path.join(self.source_folder, "taskflow"),
            dst=os.path.join(self.package_folder, "include", "taskflow"),
        )

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("pthread")

        self.cpp_info.set_property("cmake_file_name", "Taskflow")
        self.cpp_info.set_property("cmake_target_name", "Taskflow::Taskflow")
