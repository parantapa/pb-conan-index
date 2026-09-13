# pb-conan-index

PB's personal conan recipes index.

This repository holds conan recipes for two kinds of package.
The first is missing from conancenter.
The second needs a version or a configuration conancenter does not provide.
It follows the same layout as
[conan-center-index](https://github.com/conan-io/conan-center-index),
so conan can consume it directly as a local recipes index remote.

## Setup

The local recipes index remote requires conan 2.2 or newer.

Clone the repository and register it as a remote:

```sh
git clone https://github.com/parantapa/pb-conan-index
conan remote add pb-conan-index /path/to/pb-conan-index --type=local-recipes-index
```

Check that conan sees the recipes:

```sh
conan list "*" -r=pb-conan-index
```

Pull updates with `git pull`.
The remote reads the working tree, so no further conan command is needed.

## Usage

Require the packages as usual, for example in a `conanfile.txt`:

```ini
[requires]
taskflow/4.1.0.pci
zpp_bits/4.7.6.pci

[generators]
CMakeDeps
CMakeToolchain
```

Then build the dependencies, since this index serves recipes only:

```sh
conan install . --build=missing
```

## Documentation

| Document | Contents |
| --- | --- |
| [Recipes](docs/reference/recipes.md) | The packages this index provides, what each recipe builds, and the cmake target each one exports. |
| [Repository layout](docs/reference/repository-layout.md) | The files that make up a recipe. |
| [The linkage of the hdf5 filters](docs/explanation/hdf5-plugin-linkage.md) | Why a filter links against hdf5 the way it does. |
| [The Stan Math dependencies](docs/explanation/stan-math-dependencies.md) | Why eigen is held back, and what the sundials and tbb patches are for. |
| [The libtorch build configuration](docs/explanation/libtorch-build-configuration.md) | Why so much of PyTorch is left out, how the source is assembled, and why the cmake target force links. |

Report a bug at <https://github.com/parantapa/pb-conan-index/issues>.

## License

MIT. See [LICENSE](LICENSE).
