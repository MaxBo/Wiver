# -*- coding: utf-8 -*-
"""
Created on Fri Jun 10 20:33:08 2016

@author: MaxBohnet
"""

from setuptools import setup, find_packages
from cythoninstallhelpers.make_cython_extensions import make_extensions

ext_modnames = ['wiver.wiver_cython',
                ]


setup(
    name="wiver",
    version="1.1",
    description="commercial trip model and pessenger demand model",

    packages=find_packages('src', exclude=['ez_setup']),
    #namespace_packages=['wiver'],

    package_dir={'': 'src'},
    package_data={'': ['*.pxd']},
    include_package_data=True,
    zip_safe=False,
    data_files=[
        ],

    extras_require=dict(
        extra=[],
        docs=[
            'z3c.recipe.sphinxdoc',
            'sphinxcontrib-requirements'
        ],
        test=[]
    ),

    install_requires=[
        'cythonarrays',
    ],
    ext_modules=make_extensions(ext_modnames),
)
