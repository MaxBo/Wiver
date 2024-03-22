from setuptools import setup
from cythonarrays.make_cython_extensions import make_extensions


package_name = 'wiver'
ext_modnames = ['wiver.wiver_cython',
                ]
further_args = {
    'wiver.wiver_cython': {"define_macros": [
        ('CYTHON_TRACE', 0),
        ('CYTHON_TRACE_NOGIL', 0),
        ("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION"),
    ]}
}

setup(
    ext_modules=make_extensions(ext_modnames, further_args=further_args),
)
