# Repository layout

Each package lives under `recipes/<package>`:

```
recipes/<package>/config.yml            versions and the folder that builds them
recipes/<package>/all/conanfile.py      the recipe
recipes/<package>/all/conandata.yml     per version source data, where present: archive url and checksum, or git url with a tag or commit
```
