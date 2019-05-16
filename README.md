
[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](http://www.gnu.org/licenses/gpl-3.0)
[![Build Status](https://travis-ci.org/MaxBo/Wiver.svg?branch=master)](https://travis-ci.org/MaxBo/Wiver)
[![Build status](https://ci.appveyor.com/api/projects/status/q0lek1t5tl5lcq29?svg=true)](https://ci.appveyor.com/project/MaxBo/wiver)
[![codecov](https://codecov.io/gh/MaxBo/Wiver/branch/master/graph/badge.svg)](https://codecov.io/gh/MaxBo/Wiver)
[![PyPI version](https://badge.fury.io/py/wiver.svg)](https://badge.fury.io/py/wiver)
[![Anaconda-Server Badge](https://anaconda.org/maxbo/wiver/badges/version.svg)](https://anaconda.org/maxbo/wiver)
[![Anaconda-LastUpdate](https://anaconda.org/maxbo/wiver/badges/latest_release_date.svg)(https://anaconda.org/maxbo/wiver)

# Wiver
# Business Trip Model

Code documentation can be found [here](https://maxbo.github.io/Wiver)

Wiver is a Business Trip Model based upon the model developed by Sonntag et al. (1998).

It is a macroscopic, tour-based model, that calculates demand matrices for different economic sectors and vehicle types.
It consists of the steps

* Tour Generation
* Destination Choice Model
* Tour Optimization (Savings Algorithm)
* Trip Balancing

The model has the following dimensions:

* n_zones: the number of transport analysis zones (TAZ)
* n_groups: the number of demand groups defined by economic sectors and vehicle types
* n_modes: the number of vehicle types
* n_savings_categories: the number of savings categories needed for the tour optimization model
* n_time_slices: the number of time slices to stratify the demand by time of day
* n_threads: the number of threads to use for parallel computation. Defaults to all available threads

```
Dimensions:                        (n_groups: 2, n_modes: 3, n_savings_categories: 10, n_threads: 2, n_time_slices: 3, n_zones: 5)
Coordinates:
  * n_groups                       (n_groups) object 'Gruppe 0' 'Gruppe 1'
  * n_modes                        (n_modes) object 'Rad' 'Pkw' 'OV'
  * n_time_slices                  (n_time_slices) object None None None
  * n_zones                        (n_zones) object 'A-Stadt' 'B-Stadt' ...
Dimensions without coordinates: n_savings_categories, n_threads
```

The input data is to be provided as a [xarray-Dataset](https://xarray.org) with the following Data variables:


*Tour Generation*

For each economic sector the number of employees per travel analysis zone (TAZ) is required.
```
    source_potential_gh            (n_groups, n_zones) float64
```

* Destination Choice Model
* Tour Optimization (Savings Algorithm)
* Trip Balancing

[Documentation](https://maxbo.github.io/Wiver/)

# Installation

The easiest way to handle dependencies is to use [conda](https://conda.io/miniconda.html).

There conda packages for python 3.5 to 3.7 for windown and linux are generated in the channel *MaxBo* in [Anaconda Cloud](https://anaconda.org/MaxBo).
```
conda create -n wiver python=3.7
activate wiver

conda config --add channels conda-forge
conda config --add channels MaxBo

conda install wiver
```

Or you install it in an virtual environment with `pip install wiver`
```
pip install cythoninstallhelpers
pip install cythonarrays
pip install wiver
```

Test the package:

```
pip install pytest-benchmark
py.test --pyargs wiver
```
