# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import os

version = '0.0.1'

setup(
    name='mapl_customization',
    version=version,
    description='Customizations Done Specifically for Mehta Automobiles Pvt Ltd',
    author='Akshay Mehta',
    author_email='mehta.akshay@gmail.com',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=("frappe",),
)
