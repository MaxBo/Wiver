
[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](http://www.gnu.org/licenses/gpl-3.0)
[![Build status](https://ci.appveyor.com/api/projects/status/q0lek1t5tl5lcq29?svg=true)](https://ci.appveyor.com/project/MaxBo/wiver)
[![Build Status](https://github.com/MaxBo/wiver/actions/workflows/python-package-conda.yml/badge.svg)](https://github.com/MaxBo/wiver/actions/workflows/python-package-conda.yml)
[![codecov](https://codecov.io/gh/MaxBo/Wiver/branch/master/graph/badge.svg)](https://codecov.io/gh/MaxBo/Wiver)
[![PyPI version](https://badge.fury.io/py/wiver.svg)](https://badge.fury.io/py/wiver)
[![Anaconda-Server Badge](https://anaconda.org/maxbo/wiver/badges/version.svg)](https://anaconda.org/maxbo/wiver)
[![Anaconda-LastUpdate](https://anaconda.org/maxbo/wiver/badges/latest_release_date.svg)](https://anaconda.org/maxbo/wiver)

# Wiver - Business Trip Model

Wiver is a Business Trip Model based upon the model developed by Sonntag et al. (1998).

It is a macroscopic, tour-based model, that calculates demand matrices for different economic sectors and vehicle types.
It consists of the steps

* Tour Generation
* Destination Choice Model
* Tour Optimization (Savings Algorithm)
* Trip Balancing

## Model Components

The model has the following dimensions:

* n_zones: the number of transport analysis zones (TAZ)
* n_groups: the number of demand groups defined by economic sectors and vehicle types
* n_time_slices: the number of time slices to stratify the demand by time of day
* n_modes: the number of vehicle types
* n_sectors: the number of economic sectors
* n_threads: the number of threads to use for parallel computation. Defaults to all available threads

```
from wiver.wiver_python import WIVER
wiver = WIVER(n_groups=3,
			  n_zones=5,
			  n_time_slices=3,
			  n_modes=3,
			  n_sectors=2)
```

The input data can to be provided as a [xarray-Dataset](https://xarray.org) with the following Data variables:

**Zones, Sectors, Modes, and Groups**

The zones have a number and optionally a name:
```
wiver.zone_no = [10, 20, 30, 40, 50]
wiver.zone_name = ['A-City', 'B-Village', 'C-Town', 'D-Factory', 'E-Site']
```

The Modes and sectors have a name:

```
wiver.modes = ['Car', 'Truck', 'Van']
wiver.sector_short = ['IND', 'SERVICE']
```
The groups have a name and are assinged to a mode and a sector:

```
wiver.group_names = ['Car_Service', 'Van_Industry', 'Truck_Industry']
wiver.modes_g = [0, 2, 1]
wiver.sector_g = [1, 0, 0]
```

**Travel time Matrix**

For each mode `m`, a travel-time matrix from zone `i` to zone `j` has to be provided:
If the matrix is the same for all modes, if can be assigned to all modes:
```
t_ij = np.ones((n_zones, n_zones))
wiver.travel_time_mij[:] = t_ij
```

Or an individual matrix is assigned to each mode:
```
wiver.travel_time_mij[0] = t_ij_car
wiver.travel_time_mij[1] = t_ij_van
wiver.travel_time_mij[1] = t_ij_truck
```

**Source and Sink Potential per Zone**

For each group `g`, a source potential for each origin zone `h` has to be given (e.g. the number of employees per sector).
For each group `g` and and destination zone `j` a sink potential is required:

```
wiver.source_potential_gh = np.ones((n_groups, n_zones))
wiver.sink_potential_gj = np.ones((n_groups, n_zones))
```

**Tour Rates and Stops per Tour**

For each group `g`, the tour rates and stops per tour are defined:
```
wiver.tour_rates_g = np.ones((n_groups))
wiver.stops_per_tour_g = np.ones((n_groups))
```

**Tour Generation**

For each group, the number of tours, that start and end in a zone, are calculated by the source_potential and the tour_rates of the group. Each tour has linking trips, which are calculated using the stops_per_tour provided.

**Destination Choice and Tour Optimization Model (Savings Algorithm)**

The destination choice model first calculates the trips from the home zone `h` of the tour to the first stop and then the linking trips from the first stop to the next stops.

For the first trip, the distance decay for each group is defined by the distance parameter `param_dist_g`:

```
param_dist_g = [-0.4, -0.2, -0.03]
```

A big negative parameter means, that destinations very close to the home zone are chosen as the first stop. A parameter close to zero means, that the travel time has low influence on the destination choice and the destinations are chosen maily by the sink potential of the destination zone.

For the linking trips, first the destination choice is calculated with the same parameter as for the first trip.
Then, a savings factor is calculated using the savings algorithm to account for tour optimization.

The savings factor is calculated using the savings-parameter

```
savings_param_g = [1.05, 1.5, np.inf]
```

the savings-parameter have to be > 1.0
A parameter close to 1 represents a high level of tour optimization (as in the case of postal services),
and the mean distance of the linking trips are small
A larger parameter means a low level of tour optimization and the linking trips are longer.
An infititive value means no tour optimization at all.

**Trip Balancing**

The model can be run with trip balancing, which ensures, that for example all customers are served.
The number of trips to a destination zone should be proportional to the sink potential of the destination zone.

The following example should illustrate the balancing algorithm:

There are in total 20 tours with 100 stops to 3 destinations starting in a depot in zone 1.
The destinations have a sink potential of `[1, 4, 5]`.
So the destinations should receive 10, 40, and 50 trips.
`target_trips_gj = [10, 40, 50]`

Without balancing, it might be that zone 1 receives more trips, because it is close to the depot,
while destinations 0 and 2 receive less trips than expected:
`trips_gj = [5, 60, 35]`.
Then a balancing factor is calculated, wich increases the probability,
that destinations 0 and 2 are delivered and decreases the probability that a trip goes to zone 1.
After some iterations, the model should converge for a group and stops if the threshold
(relative difference between target trips and modelled trips) or the maximum number of iterations are reached:

```
trips_gj = [9, 43, 48]
target_trips_gj = [10, 40, 50]
difference = [-1, 3, -2]
relative_difference = [-0.1, 0.075, -0.04]
(abs(relative_difference) < threshold).all()

wiver.calc_with_balancing(max_iterations=10, threshold=0.1)
```

The number of iterations needed to converge for a group is stored in `wiver.converged_g`.
A value of 0 means, that the trip balancing for the group did not converge yet.


**Time Series**
The results of the model can be calculated for different time slices.
In the morning, most tours start in the depot, during the day, there are more linking trips between the destinations and in the afternoon the vehicles return to their deopt (home zone).
The time series for each group are defined for starting, linking, and ending trips.
In the following example we have 2 groups and 3 time-slices (morning, day, evening).

```
wiver.time_series_starting_trips_gs = np.array([[5, 4, 1],
												[10, 0, 0]])
wiver.time_series_linking_trips_gs = np.array([[2, 3, 2],
											   [2, 5, 3]])
wiver.time_series_ending_trips_gs = np.array([[0, 3, 7],
											  [0, 0, 9]])
```

For group 0, 50% of the tours start in the morning, 40% during the day and 10% in the evening. For group 1, all tours start in the morning.
The linking trips are carried out during the day.
The ending trips, which return to the depot happen to 30% during the day and to 70% in the evening for group 0 and happen all in the evening for group 1.

## Code Documentation
[Documentation](https://maxbo.github.io/Wiver/)

# Installation

The easiest way to handle dependencies is to use [conda](https://conda.io/miniconda.html).

There conda packages for python 3.6 to 3.10 for windows and linux are generated in the channel *MaxBo* in [Anaconda Cloud](https://anaconda.org/MaxBo).
```
conda create -n wiver -c MaxBo python=3.10 wiver
conda activate wiver

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
