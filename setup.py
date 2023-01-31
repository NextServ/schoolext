from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in schoolext/__init__.py
from schoolext import __version__ as version

setup(
	name="schoolext",
	version=version,
	description="School Extension",
	author="SERVIO Enterprise",
	author_email="robert@serviotech.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
