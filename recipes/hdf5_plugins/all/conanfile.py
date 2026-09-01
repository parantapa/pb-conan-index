# type: ignore
import os
import textwrap

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMakeToolchain, CMakeDeps, CMake, cmake_layout
from conan.tools.files import copy, get, rename, save


class HDF5PluginsRecipe(ConanFile):
    name = "hdf5_plugins"

    description = "HDF5 plugins: compression filters loaded by hdf5 at run time"
    license = "BSD-3-Clause"
    url = "https://github.com/parantapa/pb-conan-index"
    homepage = "https://github.com/HDFGroup/hdf5_plugins"
    topics = (
        "hdf5",
        "compression",
        "filter",
        "plugin",
        "codec",
    )

    # The filters this recipe can build,
    # named after the ENABLE_<FILTER> option that upstream cmake uses.
    _filters = (
        "bitgroom",
        "bitround",
        "blosc",
        "blosc2",
        "bshuf",
        "bzip2",
        "granular_bitround",
        "jpeg",
        "lz4",
        "lzf",
        "zfp",
        "zstd",
    )

    # Almost everything here is a loadable module rather than a library.
    # The one thing a consumer links against is the static library
    # that carries the property list interface of the zfp filter,
    # so this is what the package type describes.
    package_type = "static-library"
    settings = "os", "compiler", "build_type", "arch"
    options = {_filter: [True, False] for _filter in _filters}
    default_options = dict(
        {_filter: True for _filter in _filters},
        **{"hdf5/*:shared": True},
    )

    def requirements(self):
        # The zfp filter installs headers that include hdf5.h,
        # and a static library that calls into hdf5,
        # so a consumer of either needs both from hdf5 as well.
        self.requires("hdf5/1.14.6", transitive_headers=True, transitive_libs=True)

    def validate(self):
        if (
            not self.dependencies["hdf5"].options.shared
            and self.settings.os == "Windows"
        ):
            raise ConanInvalidConfiguration(
                "hdf5_plugins requires hdf5/*:shared=True on Windows. "
                "Against a static hdf5 the filters are built "
                "with the hdf5 symbols left undefined, "
                "which a dll cannot be."
            )

    @property
    def _upstream_version(self):
        # The version of this index carries a suffix that upstream does not.
        return self.version.removesuffix(".pci")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

        # Every path in the release tarball starts with a "./" component,
        # and that is the component strip_root takes off,
        # so the archive still unpacks into a directory of its own.
        unpacked = os.path.join(
            self.source_folder, f"hdf5_plugins-{self._upstream_version}"
        )
        for entry in os.listdir(unpacked):
            rename(
                self,
                os.path.join(unpacked, entry),
                os.path.join(self.source_folder, entry),
            )
        os.rmdir(unpacked)

    def layout(self):
        cmake_layout(self, src_folder="hdf5_plugins")

    def generate(self):
        deps = CMakeDeps(self)
        deps.generate()

        # Upstream looks for an hdf5 installed by the HDF Group cmake build,
        # whose config file, components and targets
        # are not the ones conan generates.
        # Defining H5PL_HDF5_HEADER takes the branch upstream uses
        # when the plugins are built as part of a larger project:
        # the search is skipped and the hdf5 target is taken as given.
        support = textwrap.dedent("""\
            find_package(HDF5 REQUIRED CONFIG)
            set(H5PL_HDF5_HEADER "h5pubconf.h")
            set(H5PL_HDF5_INCLUDE_DIRS ${HDF5_INCLUDE_DIRS})
            """)

        if self.dependencies["hdf5"].options.shared:
            support += "set(H5PL_HDF5_LINK_LIBS hdf5::hdf5)\n"
        else:
            # A filter is loaded into a process that already runs hdf5.
            # Linking a static hdf5 into the filter
            # would put a second copy of the library in that process,
            # and a filter that calls back into hdf5 from its set_local
            # callback then fails to recognise the caller's property list.
            # So the filters are given the hdf5 headers but no hdf5 to link,
            # and their hdf5 symbols are resolved from the loading process.
            support += textwrap.dedent("""\
                add_library(h5pl_hdf5_headers INTERFACE)
                target_include_directories(
                    h5pl_hdf5_headers INTERFACE ${HDF5_INCLUDE_DIRS})
                set(H5PL_HDF5_LINK_LIBS h5pl_hdf5_headers)
                """)

        hdf5_support = os.path.join(self.generators_folder, "conan_hdf5_support.cmake")
        save(self, hdf5_support, support)

        tc = CMakeToolchain(self)

        # cmake reads this right after the top level project() call,
        # which is before upstream looks for hdf5.
        tc.cache_variables["CMAKE_PROJECT_TOP_LEVEL_INCLUDES"] = hdf5_support.replace(
            "\\", "/"
        )

        # The release tarball ships the source of every compression library
        # the filters need under libs.
        # TGZ builds each filter against the bundled copy through FetchContent,
        # which is the configuration upstream releases and tests,
        # and which needs no network access.
        # The bundled libraries are built static
        # and end up inside the filter that uses them.
        tc.cache_variables["H5PL_ALLOW_EXTERNAL_SUPPORT"] = "TGZ"
        tc.cache_variables["H5PL_COMP_TGZPATH"] = os.path.join(
            self.source_folder, "libs"
        ).replace("\\", "/")

        for _filter in self._filters:
            tc.variables[f"ENABLE_{_filter.upper()}"] = bool(
                self.options.get_safe(_filter)
            )

        tc.variables["H5PL_BUILD_TESTING"] = False
        tc.variables["H5PL_BUILD_EXAMPLES"] = False

        # The community filters are all commented out upstream.
        tc.variables["H5PL_COMMUNITY"] = False

        # Conan packages the build, so the cpack setup is only overhead.
        # Leaving it out also keeps INSTALL_SUPPORT
        # from rewriting CMAKE_INSTALL_PREFIX.
        tc.variables["H5PL_CPACK_ENABLE"] = False

        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        licenses = os.path.join(self.package_folder, "licenses")
        copy(self, "COPYING", src=self.source_folder, dst=licenses)
        copy(
            self,
            "*/Additional_Legal/*",
            src=self.source_folder,
            dst=licenses,
            excludes="community/*",
        )
        copy(self, "ZFP/LICENSE", src=self.source_folder, dst=licenses)
        copy(self, "ZFP/H5Z-ZFP/LICENSE", src=self.source_folder, dst=licenses)
        copy(self, "BSHUF/src/lib/lz4/LICENSE", src=self.source_folder, dst=licenses)

        cmake = CMake(self)
        cmake.install()

        if self.options.zfp:
            # Besides the plugin, the zfp filter installs a static library
            # holding the property list interface that H5Zzfp.h declares.
            # That library calls into the zfp codec,
            # which upstream builds through FetchContent
            # and leaves out of the install,
            # so the archive it was linked against is taken from the build
            # and shipped next to it.
            copy(
                self,
                "*zfp.a",
                src=os.path.join(self.build_folder, "bin"),
                dst=os.path.join(self.package_folder, "lib"),
                keep_path=False,
            )
            copy(
                self,
                "*zfp.lib",
                src=os.path.join(self.build_folder, "bin"),
                dst=os.path.join(self.package_folder, "lib"),
                keep_path=False,
            )

    def package_info(self):
        self.cpp_info.bindirs = []

        if self.options.zfp:
            # H5Zzfp.h declares two ways to reach the zfp filter.
            # The macros of H5Zzfp_plugin.h fill in a cd_values array
            # for the filter that hdf5 loads from the plugin directory,
            # and need nothing to link against.
            # The functions of H5Zzfp_lib.h and H5Zzfp_props.h
            # register the filter with hdf5 directly instead,
            # and live in h5zzfp,
            # which in turn calls into the zfp codec it was built against.
            self.cpp_info.libs = ["h5zzfp", "zfp"]
            self.cpp_info.libdirs = ["lib"]
            if self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.system_libs = ["m"]
        else:
            # Every other filter is dlopened by hdf5,
            # so nothing is left for a consumer to link or include.
            self.cpp_info.libs = []
            self.cpp_info.libdirs = []
            self.cpp_info.includedirs = []

        if not self.dependencies["hdf5"].options.shared:
            # Against a static hdf5 the filters carry no hdf5 of their own
            # and look the symbols up in the process that loads them,
            # which only finds them
            # if the program put its own symbols in the dynamic symbol table.
            if self.settings.os == "Macos":
                self.cpp_info.exelinkflags = ["-Wl,-export_dynamic"]
            elif self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.exelinkflags = ["-rdynamic"]

        # hdf5 searches this path, and then its build time default,
        # when it meets a filter it does not know.
        plugin_folder = os.path.join(self.package_folder, "lib", "plugin")
        self.runenv_info.append_path("HDF5_PLUGIN_PATH", plugin_folder)
        self.buildenv_info.append_path("HDF5_PLUGIN_PATH", plugin_folder)
