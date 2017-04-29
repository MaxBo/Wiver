# -*- coding: utf-8 -*-
"""
Created on Fri Jun 10 21:00:21 2016

@author: MaxBohnet
"""

import pytest
import xarray as xr
import numpy as np
import pandas as pd
import os
import orca
from cythonarrays.converters.xarray2netcdf import xr2netcdf
from wiver.mode_destination_choice import calc_mode_destination_choice
from wiver.tests.filename_definitions import dataset_fn, zones_fn



@pytest.fixture(scope='class')
def zones():
    """Create a example zones Table"""
    zones = pd.DataFrame()
    ids = pd.Series(data=[10, 20, 30], dtype='i4', name='vznr')
    names = pd.Series(['A-Stadt', 'B-Dorf', 'EKZ'], name='name')
    jobs = pd.Series([750, 0, 250], name='jobs')
    ew = pd.Series([500, 1500, 0], name='ew')
    vfl = pd.Series([100., 0, 200.], name='vfl')
    for serie in (ids, names, jobs, ew, vfl):
        zones[serie.name] = serie
    fn = os.path.join(os.path.dirname(__file__),
                      'zones.h5')
    zones.to_hdf(fn, 'data', complevel=2, complib='blosc')
    return zones


@pytest.fixture(scope='class')
def t_pkw():
    arr = np.array([
        [5, 10, 20],
        [10, 5, 30],
        [20, 30, 5]
    ], dtype='f8')
    return arr


@pytest.fixture(scope='class')
def t_ov():
    arr = np.array([
        [10, 15, 25],
        [15, 10, 20],
        [25, 20, 10]
    ], dtype='f8')
    return arr


@pytest.fixture(scope='class')
def modes():
    modes = pd.Series(data=['car', 'ov'], name='mode')
    return modes


@pytest.fixture(scope='class',
                params=[0.2, 1.2, 5],
                ids=['weit', 'mittel', 'nah'])
def beta_jobs(request):
    """
    different values for beta_jobs
    """
    return request.param


@pytest.fixture(scope='class', params=[0.5])
def beta_ov(request):
    """
    different values for ov
    """
    return request.param


class TestDataArray:
    """Test functions on a Data Array"""
    def create_skims(self, zones, modes, t_pkw, t_ov):
        n_zones = len(zones)
        arr = np.empty((modes.size, n_zones, n_zones), dtype='f8')
        da = xr.DataArray(arr,
                          coords=[modes, zones.vznr, zones.vznr],
                          dims=[modes.name, 'origin', 'destination'],
                          name='skims')
        da.sel(mode='car')[:] = t_pkw
        da.sel(mode='ov')[:] = t_ov
        return da

    def test_01_skim_creation(self, zones, modes, t_pkw, t_ov, beta_ov):
        da = self.create_skims(zones, modes, t_pkw, t_ov)
        ds = da.to_dataset()
        ds['jobs'] = xr.DataArray(zones.jobs,
                                  coords=[zones.vznr],
                                  dims=(['destination']))
        ds['vfl'] = xr.DataArray(zones.vfl,
                                 coords=[zones.vznr],
                                 dims=(['destination']))
        ds['ew'] = xr.DataArray(zones.ew,
                                coords=[zones.vznr],
                                dims=(['origin']))
        ds['mode_cons'] = xr.DataArray([0, beta_ov],
                                       coords=[modes],
                                       dims=(['mode']))
        ds['beta_t'] = xr.DataArray([-0.1, -0.08],
                                    coords=[modes],
                                    dims=(['mode']))
        fn = os.path.join(os.path.dirname(__file__),
                          'example_dataset.h5')
        xr2netcdf(ds, fn)

    def test_02_variables(self):
        """Test reading the datasets"""
        print(orca.eval_variable('beta_jobs'))
        print(orca.eval_variable('dataset_fn'))
        print(orca.eval_variable('zones_fn'))
        print(orca.eval_variable('tdm_dataset'))
        zones = orca.eval_variable('zones')
        z = zones.to_frame()

    def test_03_mode_destination_choice(self, beta_jobs):
        orca.add_injectable('beta_jobs', beta_jobs)
        orca.eval_step('calc_mode_destination_choice')
