# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
        install_requires = f.read().strip().split('\n')

from mapl_customization import __version__ as version

setup(
    name='mapl_customization',
    version=version,
    description='Customizations Done Specifically for Mehta Automobiles Pvt Ltd',
    author='Akshay Mehta',
    author_email='mehta.akshay@gmail.com',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires
)
