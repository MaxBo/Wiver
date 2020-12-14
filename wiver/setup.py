# -*- coding: utf-8 -*-
"""
Created on Fri Jun 10 20:33:08 2016

@author: MaxBohnet
"""

from setuptools import setup, find_packages
from cythoninstallhelpers.make_cython_extensions import make_extensions
from cythoninstallhelpers.get_version import get_version


package_name = 'wiver'
version = get_version(package_name, __file__)
ext_modnames = ['wiver.wiver_cython',
                ]


setup(
    name=package_name,
    version=version,
    description="commercial trip model and pessenger demand model",

    packages=find_packages('src', exclude=['ez_setup']),
    #namespace_packages=['wiver'],

    package_dir={'': 'src'},
    package_data={'': ['*.pxd']},
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'cythonarrays',
        'matrixconverters',
    ],
    ext_modules=make_extensions(ext_modnames),
)
