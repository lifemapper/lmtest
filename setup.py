# -*- coding: utf-8 -*-
"""Module setup file for packaging and installation."""
from setuptools import setup

with open('README.md') as f:
    readme = f.read()


with open('LICENSE') as f:
    module_license = f.read()

setup(
    name='lm_test',
    version='1.0.0-beta.1',
    description='Lifemapper Testing Library',
    long_description=readme,
    author='CJ Grady',
    author_email='cjgrady@ku.edu',
    url='https://github.com/lifemapper/lm_test',
    license=module_license,
)
