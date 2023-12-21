from setuptools import setup
from cythonarrays.make_cython_extensions import make_extensions


package_name = 'wiver'
ext_modnames = ['wiver.wiver_cython',
                ]

setup(
    ext_modules=make_extensions(ext_modnames),
)
