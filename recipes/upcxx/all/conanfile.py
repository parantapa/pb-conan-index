# type: ignore
import glob
import json
import os
import re
import shlex
from collections.abc import Callable
from io import StringIO

from conan import ConanFile
from conan.errors import ConanException, ConanInvalidConfiguration
from conan.tools.files import copy, get, load, rename, save
from conan.tools.build import build_jobs
from conan.tools.env import VirtualBuildEnv
from conan.tools.gnu import PkgConfig
from conan.tools.layout import basic_layout


class UpcxxRecipe(ConanFile):
    name = "upcxx"

    description = (
        "UPC++: a C++ library for Partitioned Global Address Space programming, "
        "built on GASNet-EX"
    )
    license = "BSD-3-Clause-LBNL"
    url = "https://github.com/parantapa/pb-conan-index"
    homepage = "https://upcxx.lbl.gov"
    topics = (
        "pgas",
        "hpc",
        "rpc",
        "rma",
        "gasnet",
        "distributed-computing",
    )

    # The GASNet-EX conduits this recipe enables or disables explicitly.
    # The mpi conduit is not listed here.
    # The mpi option controls it.
    _conduits = ("smp", "udp", "ibv", "ucx", "ofi")

    # The conduits whose job spawner can be PMI.
    # The udp conduit has no spawner option.
    _pmi_conduits = ("smp", "ibv", "ucx", "ofi")

    # The flags of every code mode, thread mode and network,
    # relative to the package folder.
    _flags_file = os.path.join("share", "conan", "upcxx-flags.json")

    package_type = "static-library"
    settings = "os", "arch", "compiler", "build_type"
    options = dict(
        {_conduit: [True, False] for _conduit in _conduits},
        mpi=[True, False],
        pmi=[True, False],
        launcher=["prterun", "srun"],
        hwloc=[True, False],
        network=["auto", *_conduits, "mpi"],
        threadmode=["seq", "par"],
    )
    default_options = dict(
        {_conduit: _conduit == "smp" for _conduit in _conduits},
        mpi=False,
        pmi=True,
        launcher="prterun",
        hwloc=True,
        network="auto",
        threadmode="seq",
    )

    @property
    def _enabled_networks(self) -> list[str]:
        networks = [c for c in self._conduits if self.options.get_safe(c)]
        if self.options.mpi:
            networks.append("mpi")
        return networks

    @property
    def _network(self) -> str:
        # The default network of the upcxx compiler wrapper,
        # and the network whose flags package_info reports to consumers.
        # Without an explicit choice it is the first enabled network
        # in the order of _conduits, which puts smp first.
        if self.options.network != "auto":
            return str(self.options.network)
        return self._enabled_networks[0]

    def config_options(self) -> None:
        if self.settings.os != "Linux":
            del self.options.ibv
            del self.options.ucx

    def configure(self) -> None:
        if not self.options.pmi:
            self.options.rm_safe("launcher")

    def layout(self) -> None:
        basic_layout(self, src_folder="src")

    def package_id(self) -> None:
        # The install holds both the debug and the opt code mode,
        # and both the seq and the par thread mode.
        # build_type and threadmode only pick
        # which of them package_info reports,
        # so neither changes the binary.
        del self.info.settings.build_type
        del self.info.options.threadmode

    def validate(self) -> None:
        if self.settings.os not in ("Linux", "FreeBSD", "Macos"):
            raise ConanInvalidConfiguration(
                f"UPC++ does not support {self.settings.os}."
            )
        if not self._enabled_networks:
            raise ConanInvalidConfiguration(
                "Enable at least one network: smp, udp, ibv, ucx, ofi or mpi."
            )
        if self._network not in self._enabled_networks:
            raise ConanInvalidConfiguration(
                f"network={self._network} is not an enabled network."
            )

    def source(self) -> None:
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def _system_prefix(self, package: str) -> str:
        # The HPC libraries come from the system, not from conan.
        # pkg-config finds their install prefix.
        # Debian, for one, installs pmix under its own prefix
        # instead of /usr.
        try:
            return PkgConfig(self, package).variables["prefix"]
        except Exception as error:
            raise ConanInvalidConfiguration(
                f"Cannot find the system {package} through pkg-config: {error}"
            ) from error

    def _build_env(self, name: str) -> str | None:
        # The [buildenv] of the profile reaches the commands that self.run starts,
        # but not os.environ of the recipe itself.
        return VirtualBuildEnv(self).vars().get(name) or os.environ.get(name)

    def _compilers(self) -> tuple[str, str]:
        executables = self.conf.get(
            "tools.build:compiler_executables", default={}, check_type=dict
        )
        if self.settings.compiler in ("clang", "apple-clang"):
            default_cc, default_cxx = "clang", "clang++"
        else:
            default_cc, default_cxx = "gcc", "g++"
        cc = executables.get("c") or self._build_env("CC") or default_cc
        cxx = executables.get("cpp") or self._build_env("CXX") or default_cxx
        if self.options.mpi:
            cxx = self._build_env("MPICXX") or "mpicxx"
        return cc, cxx

    def _configure_args(self) -> list[str]:
        cc, cxx = self._compilers()
        args = [
            f"--prefix={self.package_folder}",
            f"--with-cc={cc}",
            f"--with-cxx={cxx}",
            "--without-cross",
            "--disable-plpa",
            "--disable-cuda",
            "--disable-hip",
            "--disable-ze",
            f"--with-default-network={self._network}",
        ]

        if self.options.mpi:
            args += ["--enable-mpi", "--enable-mpi-compat"]
        else:
            args += ["--disable-mpi", "--disable-mpi-compat", "--without-mpicc"]

        enabled = self._enabled_networks
        args += [
            f"--enable-{c}" if c in enabled else f"--disable-{c}"
            for c in self._conduits
        ]

        if self.options.pmi:
            if self.options.launcher == "srun":
                launch = "srun --mpi=pmix"
            else:
                launch = "prterun"
            # The GASNet-EX configure resolves the launcher to an absolute path.
            # PMIRUN_CMD in the environment overrides it at run time.
            # --with-pmi-version=x accepts only a PMIx client library.
            # In the launch template, %N is the number of processes,
            # %P is the program and %A is its arguments.
            args += [
                "--enable-pmi",
                f"--with-pmi-home={self._system_prefix('pmix')}",
                "--with-pmi-version=x",
                f"--with-pmirun-cmd={launch} -n %N %P %A",
            ]
            # Make PMI the spawner of every enabled conduit that supports one.
            args += [
                f"--with-{c}-spawner=pmi" for c in self._pmi_conduits if c in enabled
            ]
        else:
            args.append("--disable-pmi")

        if self.options.hwloc:
            args += [
                "--enable-hwloc",
                f"--with-hwloc-home={self._system_prefix('hwloc')}",
            ]
        else:
            args.append("--disable-hwloc")

        return args

    # Flags from the profile would reach every code mode,
    # and override the flags that tell the opt and debug code modes apart.
    # The recipe therefore runs configure itself, without AutotoolsToolchain,
    # and unsets these variables for configure, make and make install.
    _unset_flags = "unset CFLAGS CXXFLAGS CPPFLAGS LDFLAGS LIBS"

    def build(self) -> None:
        gasnet_args = self._build_env("GASNET_CONFIGURE_ARGS") or ""
        # --enable-rpath links the GASNet-EX libraries
        # with a run path to the system libraries they depend on,
        # such as a pmix installed outside the default library path.
        gasnet_args = f"--enable-rpath {gasnet_args}".strip()
        unset = self._unset_flags
        configure = shlex.join(
            [os.path.join(self.source_folder, "configure"), *self._configure_args()]
        )
        self.run(
            f"{unset}; GASNET_CONFIGURE_ARGS={shlex.quote(gasnet_args)} {configure}",
            cwd=self.build_folder,
        )
        self.run(f"{unset}; make -j{build_jobs(self)} all", cwd=self.build_folder)

    def package(self) -> None:
        self.run(f"{self._unset_flags}; make install", cwd=self.build_folder)

        licenses = os.path.join(self.package_folder, "licenses")
        copy(self, "LICENSE.txt", self.source_folder, licenses)
        copy(
            self,
            "license.txt",
            os.path.join(self.package_folder, "gasnet.opt", "share", "doc", "GASNet"),
            os.path.join(licenses, "GASNet"),
        )

        # See "The upstream cmake package files" in the developer notes.
        rename(
            self,
            os.path.join(self.package_folder, "share", "cmake"),
            os.path.join(self.package_folder, "share", "_orig_cmake"),
        )

        self._make_relocatable()
        # The flags come from the relocated scripts,
        # so the check also covers a path that the parser left absolute.
        save(
            self,
            os.path.join(self.package_folder, self._flags_file),
            json.dumps(self._collect_flags(), indent=2, sort_keys=True),
        )
        self._check_relocatable()

    # The token that stands for the install prefix in the inner upcxx-meta scripts.
    # The outer bin/upcxx-meta exports the variable.
    # The ":?" makes a direct run of an inner script fail
    # instead of printing paths under "/".
    _prefix_token = "${UPCXXI_INSTALL_PREFIX:?}"

    # Files that record the install prefix only as a note of the configure command.
    # Nothing reads the path back from them.
    _informational_files = ("upcxx_config.hpp", "config-details.txt")

    def _rewrite(self, path: str, rewrite: Callable[[str], str]) -> None:
        text = load(self, path)
        new_text = rewrite(text)
        if new_text == text:
            raise ConanException(f"Relocation changed nothing in {path}.")
        save(self, path, new_text)

    @staticmethod
    def _after_first_line(text: str, insert: str) -> str:
        first, rest = text.split("\n", 1)
        return f"{first}\n{insert}{rest}"

    def _make_relocatable(self) -> None:
        # See "The upcxx relocation" in the developer notes.
        prefix = self.package_folder

        def path(*parts: str) -> str:
            return os.path.join(prefix, *parts)

        # upcxx.sh sources the outer upcxx-meta, and users run it,
        # and BASH_SOURCE names the file in both cases.
        # The path can be relative, such as ./upcxx-meta or bin//upcxx-meta,
        # so the prefix is the folder of the script and then its parent.
        # Stripping the last two components would give bin for ./upcxx-meta.
        outer_preamble = (
            '_upcxxi_self="${BASH_SOURCE[0]}"\n'
            '[[ "$_upcxxi_self" == /* ]] || _upcxxi_self="$PWD/$_upcxxi_self"\n'
            '_upcxxi_self="${_upcxxi_self%/*}"\n'
            'if [[ "$_upcxxi_self" == */bin ]]; then\n'
            '  export UPCXXI_INSTALL_PREFIX="${_upcxxi_self%/bin}"\n'
            "else\n"
            '  export UPCXXI_INSTALL_PREFIX="$_upcxxi_self/.."\n'
            "fi\n"
            f"_upcxxi_token='{self._prefix_token}'\n"
        )
        dump_echo = '    echo "$line"\n'
        # The loop avoids ${line//pattern/replacement}.
        # Bash 4.2 and older, such as the /bin/bash of macOS,
        # keep the quotes of a quoted replacement in the output,
        # and bash 5.2 expands a "&" in an unquoted one.
        # The quotes in the patterns make bash match the token literally.
        dump_echo_new = (
            '    _upcxxi_rest="$line"\n'
            "    line=\n"
            '    while [[ "$_upcxxi_rest" == *"$_upcxxi_token"* ]]; do\n'
            '      line="$line${_upcxxi_rest%%"$_upcxxi_token"*}'
            '$UPCXXI_INSTALL_PREFIX"\n'
            '      _upcxxi_rest="${_upcxxi_rest#*"$_upcxxi_token"}"\n'
            "    done\n"
            '    echo "$line$_upcxxi_rest"\n'
        )

        def outer_meta(text: str) -> str:
            if text.count(dump_echo) != 1:
                raise ConanException("bin/upcxx-meta: the DUMP loop changed upstream.")
            text = text.replace(dump_echo, dump_echo_new)
            text = text.replace(f'"{prefix}/', '"${UPCXXI_INSTALL_PREFIX}/')
            return self._after_first_line(text, outer_preamble)

        self._rewrite(path("bin", "upcxx-meta"), outer_meta)

        # Each inner upcxx-meta assigns one variable per line.
        # Turning a single quoted value into a double quoted one is safe
        # only when the value holds nothing
        # that double quotes treat specially.
        single_quoted = re.compile(r"^(\w+)='([^']*)'$")

        def inner_meta(text: str) -> str:
            lines = []
            for line in text.split("\n"):
                if prefix in line:
                    match = single_quoted.match(line)
                    if match:
                        if re.search(r'["$`\\]', match.group(2)):
                            raise ConanException(
                                f"upcxx-meta: cannot double quote {match.group(1)}."
                            )
                        line = f'{match.group(1)}="{match.group(2)}"'
                    elif re.match(r"^\w+='", line):
                        # The token would stay inside single quotes,
                        # where it does not expand.
                        raise ConanException(
                            f"upcxx-meta: cannot relocate the line {line!r}."
                        )
                    line = line.replace(prefix, self._prefix_token)
                lines.append(line)
            return "\n".join(lines)

        for meta in glob.glob(path("upcxx.*", "bin", "upcxx-meta")):
            self._rewrite(meta, inner_meta)

        # The compiler wrapper finds bin from its own path.
        # The loop follows a symbolic link to the wrapper back into the package.
        # Plain readlink exists on Linux, macOS and FreeBSD, and readlink -f does not.
        wrapper_preamble = (
            '_upcxxi_self="${BASH_SOURCE[0]}"\n'
            'while [[ -L "$_upcxxi_self" ]]; do\n'
            '  _upcxxi_link="$(readlink "$_upcxxi_self")"\n'
            '  [[ "$_upcxxi_link" == /* ]] || '
            '_upcxxi_link="$(dirname "$_upcxxi_self")/$_upcxxi_link"\n'
            '  _upcxxi_self="$_upcxxi_link"\n'
            "done\n"
            '_upcxxi_bin="$(cd -P "$(dirname "$_upcxxi_self")" && pwd -P)"\n'
        )
        self._rewrite(
            path("bin", "upcxx"),
            lambda text: self._after_first_line(
                text.replace(f'"{prefix}/bin/', '"$_upcxxi_bin/'), wrapper_preamble
            ),
        )
        self._rewrite(
            path("bin", "test-upcxx-install.sh"),
            lambda text: self._after_first_line(
                text.replace(prefix, "$_upcxxi_prefix"),
                '_upcxxi_prefix="$(cd -P "$(dirname "$0")/.." && pwd -P)"\n',
            ),
        )

        # Each GASNet-EX build has its own prefix, gasnet.opt or gasnet.debug.
        gasnet = re.compile(re.escape(prefix) + r"/gasnet\.(?:opt|debug)")

        # pkg-config sets pcfiledir to the folder of the .pc file,
        # which is <gasnet prefix>/lib/pkgconfig.
        for pc in glob.glob(path("gasnet.*", "lib", "pkgconfig", "*.pc")):
            self._rewrite(pc, lambda text: gasnet.sub("${pcfiledir}/../..", text))

        # A .mak file sets GASNET_PREFIX before it includes anything,
        # so the last word of MAKEFILE_LIST is the .mak file itself.
        # The := keeps the value from changing at a later include.
        for mak in glob.glob(
            path("gasnet.*", "include", "**", "*.mak"), recursive=True
        ):
            gasnet_root = path(os.path.relpath(mak, prefix).split(os.sep)[0])
            depth = len(
                os.path.relpath(os.path.dirname(mak), gasnet_root).split(os.sep)
            )
            up = "/.." * depth
            self._rewrite(
                mak,
                lambda text, up=up: re.sub(
                    r"^GASNET_PREFIX = " + gasnet.pattern + r"$",
                    lambda _: f"GASNET_PREFIX := $(abspath $(dir $(lastword $(MAKEFILE_LIST))){up})",
                    text,
                    flags=re.MULTILINE,
                ),
            )

        # The modulefile sits at share/modulefiles/upcxx/<version>.
        for module in glob.glob(path("share", "modulefiles", "upcxx", "*")):
            self._rewrite(
                module,
                lambda text: self._after_first_line(
                    text.replace(f'"{prefix}', '"$upcxx_prefix'),
                    "set upcxx_prefix [file normalize "
                    "[file join [file dirname [info script]] .. .. ..]]\n",
                ),
            )

    def _check_relocatable(self) -> None:
        # See "The install prefix check" in the developer notes.
        prefix = self.package_folder.encode()
        left = []
        for root, _, files in os.walk(self.package_folder):
            for name in files:
                if name in self._informational_files:
                    continue
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

    def _collect_flags(self) -> dict[str, dict[str, list[str]]]:
        # See "The upcxx flags file" and "The upcxx relocation"
        # in the developer notes.
        flags = {}
        for codemode in ("debug", "opt"):
            for threadmode in ("seq", "par"):
                for network in self._enabled_networks:
                    key = f"{codemode}.{threadmode}.{network}"
                    flags[key] = self._parse_meta(
                        {
                            "UPCXX_CODEMODE": codemode,
                            "UPCXX_THREADMODE": threadmode,
                            "UPCXX_NETWORK": network,
                        }
                    )
        return flags

    def _meta_variable(self, selection: dict[str, str], variable: str) -> list[str]:
        meta = os.path.join(self.package_folder, "bin", "upcxx-meta")
        env = " ".join(f"{name}={value}" for name, value in selection.items())
        output = StringIO()
        self.run(f"env {env} {shlex.quote(meta)} {variable}", stdout=output, quiet=True)
        return shlex.split(output.getvalue())

    def _parse_meta(self, selection: dict[str, str]) -> dict[str, list[str]]:
        package = os.path.realpath(self.package_folder)

        def relative(path: str) -> str | None:
            path = os.path.realpath(path)
            if os.path.commonpath([path, package]) == package:
                return os.path.relpath(path, package)
            return None

        result = {
            "defines": [],
            "includedirs": [],
            "cxxflags": [],
            "libdirs": [],
            "libs": [],
            "system_libs": [],
            "linkflags": [],
        }

        for token in self._meta_variable(selection, "CPPFLAGS"):
            if token.startswith("-D"):
                result["defines"].append(token[2:])
            elif token.startswith("-I") and relative(token[2:]) is not None:
                result["includedirs"].append(relative(token[2:]))
            else:
                result["cxxflags"].append(token)

        # The compiler adds its own runtime support library,
        # and the directory of it depends on the compiler that links.
        system_libs_to_skip = ("gcc",)
        for token in self._meta_variable(selection, "LIBS"):
            if token.startswith("-L"):
                folder = relative(token[2:])
                if folder is not None:
                    result["libdirs"].append(folder)
                elif not os.path.isfile(os.path.join(token[2:], "libgcc.a")):
                    result["linkflags"].append(token)
            elif token.startswith("-l"):
                name = token[2:]
                if name == "upcxx" or name.startswith("gasnet"):
                    result["libs"].append(name)
                elif name not in system_libs_to_skip:
                    result["system_libs"].append(name)
            else:
                result["linkflags"].append(token)

        # LDFLAGS repeats the optimization and warning flags of GASNet-EX.
        # Only the run path of the system libraries and -pthread
        # matter to a consumer.
        for token in self._meta_variable(selection, "LDFLAGS"):
            if token.startswith("-Wl,-rpath") or token == "-pthread":
                result["linkflags"].append(token)

        return result

    def package_info(self) -> None:
        codemode = "debug" if self.settings.build_type == "Debug" else "opt"
        key = f"{codemode}.{self.options.threadmode}.{self._network}"
        flags = json.loads(
            load(self, os.path.join(self.package_folder, self._flags_file))
        )[key]

        self.cpp_info.set_property("cmake_file_name", "UPCXX")
        self.cpp_info.set_property("cmake_target_name", "UPCXX::upcxx")
        self.cpp_info.set_property("pkg_config_name", "upcxx")

        self.cpp_info.includedirs = flags["includedirs"]
        self.cpp_info.defines = flags["defines"]
        self.cpp_info.cxxflags = flags["cxxflags"]
        self.cpp_info.libdirs = flags["libdirs"]
        self.cpp_info.libs = flags["libs"]
        self.cpp_info.system_libs = flags["system_libs"]
        self.cpp_info.sharedlinkflags = flags["linkflags"]
        self.cpp_info.exelinkflags = flags["linkflags"]
        self.cpp_info.bindirs = ["bin"]

        # upcxx-run looks for the GASNet-EX spawners under UPCXX_INSTALL.
        self.runenv_info.define_path("UPCXX_INSTALL", self.package_folder)
        self.buildenv_info.define_path("UPCXX_INSTALL", self.package_folder)
