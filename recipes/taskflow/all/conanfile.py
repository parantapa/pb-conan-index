# type: ignore
import os

from conan import ConanFile
from conan.tools.files import copy
from conan.tools.layout import basic_layout
from conan.tools.scm import Git


class TaskflowRecipe(ConanFile):
    name = "taskflow"

    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"

    def layout(self):
        basic_layout(self, src_folder="taskflow")

    def source(self):
        tag = "v" + self.version.removesuffix(".pci")

        git = Git(self)
        git.clone(url="https://github.com/taskflow/taskflow.git", target="taskflow")
        git.folder = "taskflow"
        git.checkout(commit=tag)

    def package(self):
        copy(
            self,
            "LICENSE",
            src=os.path.join(self.source_folder, "taskflow"),
            dst=os.path.join(self.package_folder, "licenses"),
        )
        copy(
            self,
            "*",
            src=os.path.join(self.source_folder, "taskflow", "taskflow"),
            dst=os.path.join(self.package_folder, "include", "taskflow"),
        )

    def package_info(self):
        self.cpp_info.bindirs = []
        self.cpp_info.libdirs = []

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("pthread")

        self.cpp_info.set_property("cmake_file_name", "Taskflow")
        self.cpp_info.set_property("cmake_target_name", "Taskflow::Taskflow")
