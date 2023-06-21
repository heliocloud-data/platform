#!/usr/bin/env python
import os
from setuptools import setup

# Utility to read the README file
def read(fname):
    return open(os.path.join(os.path.dirname(__file__),fname)).read()

setup(
    name = "scregistry",
    version = "0.3",
    author = "Johns Hopkins University Applied Physics Laboratory LLC",
    author_email = "sandy.antunes@jhuapl.edu",
    description = ("API for accessing the Shared Cloud Registry (scregistry)"
                   "specification for sharing data in and across clouds"),
    license = "MIT",
    keywords = "cloud registry AWS",
    url = "https://heliocloud.org",
    packages = ['scregistry','tests'],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        ],
    )

