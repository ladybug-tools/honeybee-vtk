import setuptools

with open("README.md", "r", encoding='utf-8') as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name="honeybee-vtk",
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    author="Ladybug Tools",
    author_email="info@ladybug.tools",
    description="Honeybee extension for translating HBJSON to VTK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ladybug-tools/honeybee-vtk",
    packages=setuptools.find_packages(exclude=["tests*"]),
    install_requires=requirements,
    include_package_data=True,
    entry_points={
        "console_scripts": ["honeybee-vtk = honeybee_vtk.cli:vtk"]
    },
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent"
    ],
    license="AGPL-3.0"
)
