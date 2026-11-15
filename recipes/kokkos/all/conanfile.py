# type: ignore
import os
import re
import shlex
from io import StringIO

from conan import ConanFile
from conan.errors import ConanException, ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, load, save
from conan.tools.gnu import PkgConfig
from conan.tools.scm import Version


class KokkosRecipe(ConanFile):
    name = "kokkos"

    description = (
        "Kokkos: a C++ performance portability programming model "
        "for parallel execution and memory abstraction"
    )
    license = "Apache-2.0 WITH LLVM-exception"
    url = "https://github.com/parantapa/pb-conan-index"
    homepage = "https://kokkos.org"
    topics = (
        "hpc",
        "parallel-computing",
        "performance-portability",
        "cuda",
        "openmp",
    )

    # The host architectures of Kokkos, as the suffix of Kokkos_ARCH_<NAME>.
    # native asks the compiler to tune for the build machine.
    _cpu_archs = (
        "native",
        "amdavx",
        "armv80",
        "armv81",
        "armv84",
        "armv84_sve",
        "armv8_thunderx",
        "armv8_thunderx2",
        "a64fx",
        "armv9_grace",
        "snb",
        "hsw",
        "bdw",
        "icl",
        "icx",
        "skl",
        "skx",
        "knc",
        "knl",
        "spr",
        "power8",
        "power9",
        "zen",
        "zen2",
        "zen3",
        "zen4",
        "zen5",
        "riscv_sg2042",
        "riscv_rva22v",
        "riscv_u74mc",
    )

    # The CUDA compute capability, as spack names it,
    # and the Kokkos_ARCH_<NAME> that builds for it.
    _cuda_archs = {
        "50": "MAXWELL50",
        "52": "MAXWELL52",
        "53": "MAXWELL53",
        "60": "PASCAL60",
        "61": "PASCAL61",
        "70": "VOLTA70",
        "72": "VOLTA72",
        "75": "TURING75",
        "80": "AMPERE80",
        "86": "AMPERE86",
        "87": "AMPERE87",
        "89": "ADA89",
        "90": "HOPPER90",
        "100": "BLACKWELL100",
        "103": "BLACKWELL103",
        "120": "BLACKWELL120",
        "121": "BLACKWELL121",
    }

    # The backends this recipe always turns off.
    _disabled_backends = ("HPX", "OPENACC", "HIP", "SYCL", "NEXTSILICON")

    # The cmake_minimum_required of upstream.
    # Upstream asks for 3.25.2 only to compile CUDA as a CMake language,
    # which this recipe does not do.
    _min_cmake = "3.22"

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "serial": [True, False],
        "openmp": [True, False],
        "threads": [True, False],
        "cuda": [True, False],
        "cuda_arch": ["none", *_cuda_archs],
        "cpu_arch": ["none", *_cpu_archs],
        "hwloc": [True, False],
        "debug": [True, False],
    }
    default_options = {
        "shared": True,
        "fPIC": True,
        "serial": True,
        "openmp": False,
        "threads": False,
        "cuda": False,
        "cuda_arch": "none",
        "cpu_arch": "none",
        "hwloc": False,
        "debug": False,
    }
    implements = ["auto_shared_fpic"]

    def configure(self) -> None:
        if not self.options.cuda:
            self.options.rm_safe("cuda_arch")

    def layout(self) -> None:
        cmake_layout(self, src_folder="src")

    def validate(self) -> None:
        check_min_cppstd(self, 20)
        if self.options.openmp and self.options.threads:
            raise ConanInvalidConfiguration(
                "Kokkos allows one host parallel backend: "
                "enable openmp or threads, not both."
            )
        if not (self.options.serial or self.options.openmp or self.options.threads):
            raise ConanInvalidConfiguration(
                "Kokkos needs a host backend: enable serial, openmp or threads."
            )
        if self.options.cuda and self.options.cuda_arch == "none":
            # Without an architecture,
            # Kokkos detects the GPU of the build machine at configure time.
            # The package would then depend on a GPU that conan does not record.
            raise ConanInvalidConfiguration(
                "cuda=True needs cuda_arch, the compute capability to build for, "
                "such as 80 or 89."
            )
        # A cmake from tool_requires is known before anything is built.
        # A cmake from the system is checked in build().
        # The get() of a dependency set raises on a missing name.
        build = self.dependencies.build
        cmake = build["cmake"] if "cmake" in build else None
        if cmake is not None and Version(cmake.ref.version) < self._min_cmake:
            raise ConanInvalidConfiguration(
                f"Building kokkos needs cmake {self._min_cmake} or newer, "
                f"tool_requires gives {cmake.ref.version}."
            )

    def source(self) -> None:
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _system_dirs(self, package: str) -> tuple[str, str]:
        # hwloc comes from the system, not from conan.
        # pkg-config finds its library and header folders.
        try:
            variables = PkgConfig(self, package).variables
            return variables["libdir"], variables["includedir"]
        except Exception as error:
            raise ConanInvalidConfiguration(
                f"Cannot find the system {package} through pkg-config: {error}"
            ) from error

    def generate(self) -> None:
        tc = CMakeToolchain(self)

        tc.cache_variables["Kokkos_ENABLE_SERIAL"] = bool(self.options.serial)
        tc.cache_variables["Kokkos_ENABLE_OPENMP"] = bool(self.options.openmp)
        tc.cache_variables["Kokkos_ENABLE_THREADS"] = bool(self.options.threads)
        tc.cache_variables["Kokkos_ENABLE_CUDA"] = bool(self.options.cuda)
        for backend in self._disabled_backends:
            tc.cache_variables[f"Kokkos_ENABLE_{backend}"] = False

        if self.options.cpu_arch != "none":
            arch = str(self.options.cpu_arch).upper()
            tc.cache_variables[f"Kokkos_ARCH_{arch}"] = True
        if self.options.cuda:
            arch = self._cuda_archs[str(self.options.cuda_arch)]
            tc.cache_variables[f"Kokkos_ARCH_{arch}"] = True

        tc.cache_variables["Kokkos_ENABLE_HWLOC"] = bool(self.options.hwloc)
        if self.options.hwloc:
            # HWLOC_ROOT would make Kokkos search only <root>/lib and <root>/lib64,
            # which misses a multiarch folder such as /usr/lib/x86_64-linux-gnu.
            # CMake searches these paths before its default ones instead.
            libdir, includedir = self._system_dirs("hwloc")
            tc.variables["CMAKE_LIBRARY_PATH"] = libdir
            tc.variables["CMAKE_INCLUDE_PATH"] = includedir

        # Upstream turns the debug checks on for a Debug build type.
        # The option decides instead, whatever the build type.
        tc.cache_variables["Kokkos_ENABLE_DEBUG"] = bool(self.options.debug)

        tc.cache_variables["Kokkos_ENABLE_TESTS"] = False
        tc.cache_variables["Kokkos_ENABLE_EXAMPLES"] = False
        tc.cache_variables["Kokkos_ENABLE_BENCHMARKS"] = False
        # See "The library directory" in the developer notes.
        tc.cache_variables["CMAKE_INSTALL_LIBDIR"] = "lib"

        tc.generate()

    def _check_cmake(self) -> None:
        # Run the cmake that CMake() runs:
        # the one tools.cmake:cmake_program names,
        # or the first on the PATH of the build environment.
        # That PATH holds the bin folders of tool_requires
        # and the [buildenv] of the profile before the system PATH.
        program = self.conf.get("tools.cmake:cmake_program", default="cmake")
        output = StringIO()
        try:
            self.run(
                f"{shlex.quote(program)} --version",
                stdout=output,
                env="conanbuild",
                quiet=True,
            )
        except ConanException as error:
            raise ConanException(
                f"Building kokkos needs cmake {self._min_cmake} or newer, "
                f"and {program} does not run: {error}"
            ) from error
        match = re.search(r"cmake version (\d+\.\d+(?:\.\d+)?)", output.getvalue())
        if match is None or Version(match.group(1)) < self._min_cmake:
            found = match.group(1) if match else "unknown"
            raise ConanException(
                f"Building kokkos needs cmake {self._min_cmake} or newer, "
                f"found {found}."
            )

    def build(self) -> None:
        self._check_cmake()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    @property
    def _cmake_folder(self) -> str:
        return os.path.join("lib", "cmake", "Kokkos")

    def package(self) -> None:
        copy(
            self,
            "LICENSE",
            self.source_folder,
            os.path.join(self.package_folder, "licenses"),
        )
        cmake = CMake(self)
        cmake.install()

        # kokkos_launch_compiler looks for nvcc_wrapper first in the package,
        # through a path relative to the config file,
        # and then in the install prefix.
        # The second hint is the absolute path of the build machine,
        # so the recipe drops it.
        common = os.path.join(
            self.package_folder, self._cmake_folder, "KokkosConfigCommon.cmake"
        )
        text = load(self, common)
        hint = f' "{self.package_folder}")'
        if text.count(hint) != 1:
            raise ConanException(
                "KokkosConfigCommon.cmake: the nvcc_wrapper hints changed upstream."
            )
        save(self, common, text.replace(hint, ")"))

        self._check_relocatable()

    def _check_relocatable(self) -> None:
        # A new option or upstream release can install
        # another file that holds the install prefix.
        # This fails the package build instead of shipping that file.
        prefix = self.package_folder.encode()
        left = []
        for root, _, files in os.walk(self.package_folder):
            for name in files:
                file = os.path.join(root, name)
                with open(file, "rb") as handle:
                    data = handle.read()
                # Binary files only carry the prefix in debug and ident strings.
                if b"\0" not in data and prefix in data:
                    left.append(os.path.relpath(file, self.package_folder))
        if left:
            raise ConanException(
                "These files still hold the install prefix: " + ", ".join(sorted(left))
            )

    def package_info(self) -> None:
        # Consumers use the upstream package files instead of CMakeDeps.
        # See "The upstream cmake package files" in the developer notes.
        self.cpp_info.set_property("cmake_find_mode", "none")
        self.cpp_info.set_property("cmake_file_name", "Kokkos")

        # The components describe the libraries to the other generators.
        # They match the upstream targets,
        # but carry no backend or architecture flags.
        core = self.cpp_info.components["kokkoscore"]
        core.libs = ["kokkoscore"]
        # CMakeToolchain puts builddirs on CMAKE_PREFIX_PATH.
        # With components, it reads them from the components only.
        core.builddirs = [self._cmake_folder]
        # Upstream adds KOKKOS_DEPENDENCE in CMakeLists.txt for kokkos_launch_compiler.
        core.defines = ["KOKKOS_DEPENDENCE"]
        if self.settings.os in ("Linux", "FreeBSD"):
            core.system_libs = ["dl", "pthread"]
        if self.options.hwloc:
            core.system_libs.append("hwloc")

        # kokkoscontainers follows the shared option.
        # Upstream always builds kokkosalgorithms and kokkossimd static.
        for name in ("kokkoscontainers", "kokkosalgorithms", "kokkossimd"):
            component = self.cpp_info.components[name]
            component.libs = [name]
            component.requires = ["kokkoscore"]
