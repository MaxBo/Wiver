# -*- coding: utf-8 -*-
"""
Created on Fri Jun 10 21:00:21 2016

@author: MaxBohnet
"""

import orca
import numpy as np
import xarray as xr
import pandas as pd


@orca.injectable()
def beta_jobs():
    return 1.0


def dataset_fn():
    return 'example_dataset.h5'


@orca.injectable()
def zones_fn():
    return 'zones.h5'


@orca.injectable()
def tdm_dataset(dataset_fn):
    """Dataset with skims and other parameters"""
    ds = xr.open_dataset(dataset_fn)
    return ds


@orca.table()
def zones(zones_fn):
    """Zones table"""
    zones = pd.read_hdf(zones_fn)
    return zones


@orca.step()
def calc_mode_destination_choice(tdm_dataset, beta_jobs):
    """
    calculate mode choice probabilities

    Parameters
    ---------
    tdm_dataset: xarray-Dataset with skim matrices, and further data
    """
    ds = tdm_dataset
    U_mode = ds.mode_cons + ds.skims * ds.beta_t
    eU_mode = np.exp(U_mode)
    denom_mode = eU_mode.sum(dim='mode')
    p_mode = eU_mode / denom_mode
    ls_mode = np.log(denom_mode)

    U_dest = np.log(ds.jobs) + beta_jobs * ls_mode
    eU_dest = np.exp(U_dest)
    denom_dest = eU_dest.sum(dim='destination')
    p_dest = eU_dest / denom_dest
    accessibility_jobs = np.log(denom_dest)

    F_ij_jobs = ds.ew * p_dest
    trips_to_workplace = F_ij_jobs.sum('origin')

    F_ijm = p_mode * F_ij_jobs
    trips_by_mode = F_ijm.sum('destination').sum('origin')
    modal_split_by_origin = (F_ijm.sum('destination') /
                             ds.ew * 100)
    modal_split_by_destination = (F_ijm.sum('origin') /
                                  trips_to_workplace * 100)

    print(trips_to_workplace, trips_by_mode,
          modal_split_by_origin, modal_split_by_destination)
