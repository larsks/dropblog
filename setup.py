#!/usr/bin/python

from setuptools import setup, find_packages

setup(
    name = 'dropblog',
    description = 'A Dropbox backed blogging platform',
    long_description = open('README.md').read(),
    author = 'Lars Kellogg-Stedman',
    author_email = 'lars@oddbit.com',
    version = "1.00",
    packages = find_packages(),
    install_requires = [
        'bottle',
        'beaker',
        'oauth',
        'dropbox',
        'markdown',
        'sqlalchemy',
        'jinja2',
        ],
    entry_points = {
#        'console_scripts': [
#            'mimecraft = mimecraft.main:main',
#            ],
        },
)

