import setuptools

# https://packaging.python.org/en/latest/guides/single-sourcing-package-version/#id1, number 4

with open("VERSION") as version_file:
  version = version_file.read().strip()

setuptools.setup(
    name="dakirby",
    version=version,
)
