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
from wiver.wiver_python import WIVER
#from wiver.tests.filename_definitions import dataset_fn, zones_fn
from pytest_benchmark.plugin import benchmark


@pytest.fixture(scope='class', params=[5, 10, ])
def n_zones(request):
    return request.param


@pytest.fixture(scope='class', params=[1, 2, 4, 8, 16])
def n_groups(request):
    return request.param


class TestWiver:
    """Test Wiver Model"""

    def create_wiver(self, n_zones, n_groups):
        """create the wiver object"""
        wiver = WIVER(n_groups, n_zones, n_modes=1,
                      n_time_slices=2, n_savings_categories=9)
        # define centroids of zones
        x = np.random.randint(0, 50, (n_zones))
        y = np.random.randint(0, 50, (n_zones))
        # calc travel time between zones
        dx = x - x[:, np.newaxis]
        dy = y - y[:, np.newaxis]
        dist = np.sqrt(dx**2 + dy**2)
        t = dist * 3 + 1

        wiver.mode_g = np.zeros((n_groups, ))

        wiver.travel_time_mij[:] = t
        # define savings intervals
        wiver.savings_bins_s = np.concatenate((np.linspace(.15, .85, 8), [1]))
        for g in range(n_groups):
            wiver.savings_weights_gs[g] = np.linspace(
                1, (g + 2), wiver.n_savings_categories)

        wiver.source_potential_gh = np.random.randint(
            0, 10, (n_groups, n_zones))
        wiver.sink_potential_gj = np.random.randint(
            0, 10, (n_groups, n_zones))
        wiver.tour_rates_g = np.linspace(1, 3, num=n_groups)
        wiver.stops_per_tour_g = np.linspace(2, 4, num=n_groups)
        return wiver

    def test_01_calc_wiver(self, n_zones, n_groups):
        """Test the results of wiver for more zones"""
        wiver = self.create_wiver(n_zones, n_groups)
        # set zone 3 to 0
        wiver.source_potential_gh[:, 3] = 0
        wiver.sink_potential_gj[:, 3] = 0
        wiver.calc()
        # assure that the total number of trips per group fits
        actual = wiver.trips_gij.sum(-1).sum(-1)
        desired = (wiver.source_potential_gh.sum(-1) *
                   wiver.tour_rates_g * (wiver.stops_per_tour_g + 1))
        np.testing.assert_almost_equal(actual, desired)
        # assure that there are no trips from and to zone 3
        np.testing.assert_equal(wiver.trips_gij[:, 3], 0)
        np.testing.assert_equal(wiver.trips_gij[:, :, 3], 0)

        # assure that at least as many tours
        # from and to home zones start and end
        desired = wiver.source_potential_gh * wiver.tour_rates_g[:, np.newaxis]
        actual = wiver.trips_gij.sum(1)
        np.testing.assert_array_equal((actual - desired) > -0.0000001, 1)

        actual = wiver.trips_gij.sum(2)
        np.testing.assert_array_equal((actual - desired) > -0.0000001, 1)

    def test_02_benchmark_wiver(self, benchmark, n_zones, n_groups):
        """Test the wiver runtime for more zones"""
        wiver = self.create_wiver(n_zones, n_groups)
        benchmark(wiver.calc)
