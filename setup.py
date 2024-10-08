from setuptools import setup, find_packages

setup(
    name="flexiznam",
    version="v0.4",
    url="https://github.com/znamlab/flexznam",
    license="MIT",
    author="Antonin Blot",
    author_email="antonin.blot@gmail.com",
    description="Znamlab tool to interact with flexilims",
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    install_requires=[
        "Click",
        "pandas",
        "portalocker",
        "webbot",
        "pyyaml",
        "flexilims @ git+ssh://git@github.com/znamlab/flexilims.git#egg=flexilims",
        "pymcms @ git+ssh://git@github.com/znamlab/pymcms.git#egg=pymcms",
        "tifffile",
        "ttkwidgets",
    ],
    entry_points="""
        [console_scripts]
        flexiznam=flexiznam.cli:cli
        """,
)
