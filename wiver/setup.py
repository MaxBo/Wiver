from setuptools import setup
from cythonarrays.make_cython_extensions import make_extensions


package_name = 'wiver'
ext_modnames = ['wiver.wiver_cython',
                ]
further_args = {'wiver.wiver_cython': {"define_macros": [
            ('CYTHON_TRACE', 1),
            ('CYTHON_TRACE_NOGIL', 1),
]}}

setup(
    ext_modules=make_extensions(ext_modnames, further_args=further_args),
)
