from setuptools import setup, find_packages

setup(
    name='flexznam',
    version='v0.1',
    url='https://github.com/znamlab/flexznam',
    license='MIT',
    author='Antonin Blot',
    author_email='antonin.blot@gmail.com',
    description='Znam lab tool to interact with flexilims',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        flexiznam=flexiznam.cli:cli
        ''',
)
