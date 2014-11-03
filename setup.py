from setuptools import setup, find_packages
from codecs import open
from os import path


here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as fh:
    long_description = fh.read()

setup(
    name='py-rt',
    version='0.2.1',

    # description
    description='Low-level API for Request tracker 4',
    long_description=long_description,

    # homepage
    url='https://github.com/dvoraka/py-rt',

    # author details
    author='dvoraka',
    author_email='alen.dvorak@gmail.com',

    # license
    license='GPLv3',

    classifiers=[
        'Development Status :: 5 - Production/Stable',

        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',

        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],

    keywords='rt4',

    packages=find_packages(exclude=['docs', 'tests']),

    install_requires=[
        'requests',
    ],

    # extras_require = {
    #     'dev': ['check-manifest'],
    #     'test': ['coverage'],
    # },

    # package_data={
    #     'sample': ['package_data.dat'],
    # },

    # entry_points={
    #     'console_scripts': [
    #         'sample=sample:main',
    #     ],
    # },
)
