from setuptools import setup, find_packages

setup(
    name='flexiznam',
    version='v0.1',
    url='https://github.com/znamlab/flexznam',
    license='MIT',
    author='Antonin Blot',
    author_email='antonin.blot@gmail.com',
    description='Znamlab tool to interact with flexilims',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'pandas',
        'webbot',
        'pyyaml',
        'flexilims @ git+ssh://git@github.com/znamlab/flexilims.git#egg=flexilims'
    ],
    entry_points='''
        [console_scripts]
        flexiznam=flexiznam.cli:cli
        ''',
)
