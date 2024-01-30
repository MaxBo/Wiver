Description
===========

Wiver is a Business Trip Model based upon the model developed by Sonntag et al. (1998).

It is a macroscopic, tour-based model, that calculates demand matrices for different economic sectors and vehicle types.
It consists of the steps::

  * Tour Generation
  * Destination Choice Model
  * Tour Optimization (Savings Algorithm)
  * Trip Balancing

The model has the following dimensions::

  * n_zones: the number of transport analysis zones (TAZ)
  * n_groups: the number of demand groups defined by economic sectors and vehicle types
  * n_modes: the number of vehicle types
  * n_time_slices: the number of time slices to stratify the demand by time of day
  * n_time_series: the number of time series
  * n_threads: the number of threads to use for parallel computation. Defaults to all available threads

  Dimensions:                        (n_groups: 2, n_modes: 3, n_threads: 2, n_sectors: 2, n_time_slices: 3, n_time_series: 5, n_zones: 5)
  Coordinates:
    * n_groups                       (n_groups) object 'Gruppe 0' 'Gruppe 1'
    * n_modes                        (n_modes) object 'Rad' 'Pkw' 'OV'
    * n_sectors                      (n_sectors) object 'Industrie' 'DL'
    * n_time_slices                  (n_time_slices) object 'morgens', 'mittags', 'abends'
    * n_time_series                  (n_time_series) object 'Hin1' 'Hin2' ... 'Home2'
    * n_zones                        (n_zones) object 'A-Stadt' 'B-Stadt' ...
  Dimensions without coordinates: n_threads

The input data is to be provided as a `xarray-Dataset <http://xarray.pydata.org/en/stable/>`_ with the following Data variables:

wiver in VISUM
################
There is a AddIn for PTV VISUM, that uses this wiver-model to calculate commercial travel demand.

The data structure of the "4-Step-Demand-Model" of VISUM is used to represent the input-
and result data of the Wiver-model.

The following Visum-Elements are represented in this wiver-package:

| VISUM    | WIVER |
| -------- | ------- |
| Zone  | Zone    |
| PersonGroup | Sector     |
| DemandStratum    | Group    |
| DemandSegment    | Mode    |
| AnalysisTimeInterval    | Time Slice    |
| TimeSeries    | Time Series    |
| NumPersons(PersonGroup) per Zone    | source_potential_gh    |
| Attraction(DemandStratum) per Zone    | sink_potential_gj    |


Tour Generation
################

For each economic sector the number of employees per travel analysis zone (TAZ) is required::

  source_potential_gh            (n_groups, n_zones) float64

Destination Choice Model
########################

For each economic sector a destination choice model is calculated between all TAZ.
The important factors are the trip attraction-potential of the destination zone j, the trip distance between zone i and j and the travel impedance coefficient which depends on the economic sector.

The destination choice model produces a matrix of trips between zones.

Tour Optimization (Savings Algorithm)
#####################################

The tour optimization step appies a savings algorithm in order to simulate that linking trips are more or less efficiently planned (depending on the economic sector).


Trip Balancing
##############

The trip balancing step checks if the number of trips to a destination zone is higher or lower than its relative trip attraction potential. In a next iteration, the attraction potential is then adjusted.

Installation
=============

The easiest way to handle dependencies is to use `conda <https://conda.io/miniconda.html/>`_.

There conda packages for python 3.8 to 3.12 for windown and linux are generated in the channel *MaxBo* in `Anaconda Cloud <https://anaconda.org/MaxBo/wiver/>`_::

  conda create -n wiver python=3.11
  activate wiver

  conda config --add channels conda-forge
  conda config --add channels MaxBo

  conda install wiver

Or you install it in an virtual environment with `pip install wiver`::

  pip install wiver

Test the package::

  pip install pytest-benchmark
  py.test --pyargs wiver
