#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os
import re


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.match("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


version = get_version('oauth_api')


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


setup(
    name="django-oauth-api",
    version=version,
    description="OAuth API for Django using Django Rest Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords='django djangorestframework oauth oauth2 oauthlib',
    author='Tomi Pajunen',
    author_email='tomi@madlab.fi',
    url='https://github.com/eofs/django-oauth-api',
    license='BSD',
    packages=find_packages(),
    python_requires=">=3.8",
    include_package_data=True,
    test_suite='runtests',
    install_requires=[
        'djangorestframework>=3.13',
        'oauthlib==2.1.0',
    ]
)
