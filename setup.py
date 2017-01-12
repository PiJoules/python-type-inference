#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


def long_description():
    with open("README.md", "r") as readme:
        return readme.read()


def packages():
    return find_packages(include=["inference*"])


def install_requires():
    with open("requirements.txt", "r") as requirements:
        return requirements.readlines()


setup(
    name="inference",
    version="0.0.1",
    description="Python Type Inference",
    long_description=long_description(),
    url="https://github.com/PiJoules/python-type-inference",
    author="Leonard Chan",
    author_email="leonardgchan@gmail.com",
    license="MIT",
    classifiers=[
        "Development Status :: 1 - Planning",
    ],
    keywords="python, type, inference",
    packages=packages(),
    install_requires=install_requires(),
    test_suite="nose.collector",
    entry_points={
        "console_scripts": [
            "dump_env=scripts.dump_env:main",
        ],
    },
)
