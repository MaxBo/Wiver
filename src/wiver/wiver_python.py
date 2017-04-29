# -*- coding: utf-8 -*-

import multiprocessing
import xarray as xr
import os
from collections import defaultdict

from cythonarrays.array_properties import _ArrayProperties
from cythonarrays.converters.save_ptv import SavePTV
from cythonarrays.converters.xarray2netcdf import xr2netcdf
import pyximport; pyximport.install()
from wiver.wiver_cython import (_WIVER,
                                DestinationChoiceError,
                                DataConsistencyError)


class WIVER(_WIVER, _ArrayProperties):
    """WIVER Commercial Trips Model"""

    def __init__(self,
                 n_groups,
                 n_zones,
                 n_savings_categories=9,
                 n_time_slices=5,
                 n_modes=4,
                 threading=True):
        super().__init__()

        self.n_modes = n_modes
        self.n_groups = n_groups
        self.n_zones = n_zones
        self.n_savings_categories = n_savings_categories
        self.n_time_slices = n_time_slices
        self.set_n_threads(threading)

        self.define_arrays()
        self.init_arrays()

    def set_n_threads(self, threading=True):
        """Set the number of threads"""
        if threading:
            self.n_threads = min(multiprocessing.cpu_count(), self.n_groups)
        else:
            self.n_threads = 1

    @classmethod
    def read_from_netcdf(cls, files):
        """Read a Wiver Model
        from a set of netcdf-Filename located in folder"""
        # create instance of self
        self = cls(n_groups=0, n_zones=0)
        # add datasets
        self.read_all_data(files)
        self.data = xr.merge((self.params, self.matrices, self.zonal_data))

        # set the dimensions
        dims = self.data.dims
        self.n_zones = dims['origins']
        self.n_groups = dims['groups']
        self.n_modes = dims['modes']
        self.n_savings_categories = dims['savings']
        self.n_time_slices = dims['time_slices']
        self.set_n_threads()

        # resize the arrays to the right dimensions
        self.init_arrays()

        self.set_arrays_from_dataset()

        return self

    def set_arrays_from_dataset(self):
        """Sets the arrays with values from the dataset"""
        ds = self.data
        # params
        self.modes = ds.modes.data
        self.groups = ds.groups.data
        self.mode_g = ds.mode_of_groups.data
        self.param_dist_g = ds.param_dist.data
        self.savings_bins_s = ds.savings_bins.data
        self.savings_weights_gs = ds.savings_weights.data
        self.tour_rates_g = ds.tour_rates.data
        self.stops_per_tour_g = ds.stops_per_tour.data
        self.time_series_starting_trips_gs = ds.time_series_starting_trips.data
        self.time_series_linking_trips_gs = ds.time_series_linking_trips.data
        self.time_series_ending_trips_gs = ds.time_series_ending_trips.data
        # zonal data
        self.source_potential_gh = ds.source_potential.data
        self.sink_potential_gj = ds.sink_potential.data
        self.zone_no = ds.zone_no.data
        self.zone_name = ds.zone_name.data
        # matrices
        self.travel_time_mij = ds.travel_time.data
        self.km_ij = ds.distance_matrix.data

        self.results = self.define_results()

    def define_arrays(self):
        """Define the arrays"""
        self.init_array('mode_g', 'n_groups', 0)

        self.init_array('savings_bins_s', 'n_savings_categories')
        self.init_array('savings_weights_gs',
                        'n_groups, n_savings_categories', 1)

        self.init_array('km_ij', 'n_zones, n_zones')
        self.init_array('travel_time_mij', 'n_modes, n_zones, n_zones')
        self.init_array('mean_distance_g', 'n_groups')
        self.init_array('mean_distance_m', 'n_modes')
        self.init_array('param_dist_g', 'n_groups', -0.1)
        self.init_array('tour_rates_g', 'n_groups', 1)
        self.init_array('stops_per_tour_g', 'n_groups', 2)

        self.init_array('source_potential_gh', 'n_groups, n_zones')
        self.init_array('sink_potential_gj', 'n_groups, n_zones')

        self.init_array('trips_gij', 'n_groups, n_zones, n_zones', 0)
        self.init_array('home_based_trips_gij',
                        'n_groups, n_zones, n_zones', 0)
        self.init_array('linking_trips_gij', 'n_groups, n_zones, n_zones', 0)
        self.init_array('p_destination_tij', 'n_threads, n_zones, n_zones', 0)
        self.init_array('p_links_tij', 'n_threads, n_zones, n_zones', 0)

        self.init_array('trips_gsij',
                        'n_groups, n_time_slices, n_zones, n_zones', 0)

        self.init_array('trips_mij',
                        'n_modes, n_zones, n_zones', 0)
        self.init_array('trips_msij',
                        'n_modes, n_time_slices, n_zones, n_zones', 0)

        self.init_array('time_series_starting_trips_gs',
                        'n_groups, n_time_slices', 1)
        self.init_array('time_series_linking_trips_gs',
                        'n_groups, n_time_slices', 1)
        self.init_array('time_series_ending_trips_gs',
                        'n_groups, n_time_slices', 1)

    def define_datasets(self):
        """Define the datasets"""
        self.params = self.define_params()
        self.matrices = self.define_matrices()
        self.zonal_data = self.define_zonal_data()
        self.results = self.define_results()

    def define_params(self):
        """Define the params"""
        ds = xr.Dataset()
        ds['modes'] = self.modes
        ds['groups'] = self.groups
        ds['mode_of_groups'] = (('groups'),
                                self.mode_g)
        ds['param_dist'] = (('groups'),
                            self.param_dist_g)
        ds['savings_bins'] = (('savings'),
                              self.savings_bins_s)
        ds['savings_weights'] = (('groups', 'savings'),
                                 self.savings_weights_gs)
        ds['tour_rates'] = (('groups'),
                            self.tour_rates_g)
        ds['stops_per_tour'] = (('groups'),
                                self.stops_per_tour_g)
        ds['time_series_starting_trips'] = (
            ('groups', 'time_slices'), self.time_series_starting_trips_gs)
        ds['time_series_linking_trips'] = (
            ('groups', 'time_slices'), self.time_series_linking_trips_gs)
        ds['time_series_ending_trips'] = (
            ('groups', 'time_slices'), self.time_series_ending_trips_gs)
        return ds

    def define_zonal_data(self):
        """Define the matrices"""
        ds = xr.Dataset()
        ds['groups'] = self.groups
        ds['zone_no'] = self.zone_no
        ds['zone_name'] = (('zone_no'), self.zone_name)
        ds['origins'] = self.zone_no
        ds['destinations'] = self.zone_no
        ds['source_potential'] = (('groups', 'origins'),
                                  self.source_potential_gh)
        ds['sink_potential'] = (('groups', 'destinations'),
                                self.sink_potential_gj)

        return ds

    def define_matrices(self):
        """Define the matrices"""
        ds = xr.Dataset()
        ds['modes'] = self.modes
        ds['origins'] = self.zone_no
        ds['destinations'] = self.zone_no
        ds['zone_no'] = self.zone_no
        ds['zone_name'] = (('zone_no'), self.zone_name)
        ds['travel_time'] = (('modes', 'origins', 'destinations'),
                             self.travel_time_mij)
        ds['distance_matrix'] = (('origins', 'destinations'),
                                 self.km_ij)

        return ds

    def define_results(self):
        """Define the results"""
        ds = xr.Dataset()
        # resulting arrays
        ds['modes'] = self.modes
        ds['groups'] = self.groups
        ds['origins'] = self.zone_no
        ds['destinations'] = self.zone_no
        ds['zone_no'] = self.zone_no
        ds['zone_name'] = (('zone_no'), self.zone_name)
        ds['trips_gij'] = (('groups', 'origins', 'destinations'),
                           self.trips_gij)
        ds['trips_gsij'] = (('groups', 'time_slices',
                             'origins', 'destinations'),
                            self.trips_gsij)
        ds['trips_mij'] = (('modes', 'origins', 'destinations'),
                           self.trips_mij)
        ds['trips_msij'] = (('modes', 'time_slices',
                             'origins', 'destinations'),
                            self.trips_msij)
        ds['mean_distance_groups'] = (('groups',),
                                      self.mean_distance_g)
        ds['mean_distance_modes'] = (('modes',),
                                     self.mean_distance_m)

        return ds

    def merge_datasets(self):
        """Merge the datasets"""
        self.data = xr.merge((self.params, self.zonal_data,
                              self.matrices, self.results))

    def save_all_data(self, wiver_files):
        """Save Dataset to netcdf-file"""
        datasets = ('params', 'zonal_data', 'matrices', 'results')
        for dataset_name in datasets:
            fn = wiver_files[dataset_name]
            self.save_data(dataset_name, fn)

    def save_data(self, dataset_name, fn):
        """Save Dataset to netcdf-file"""
        ds = getattr(self, dataset_name)
        self.logger.info('write {}'.format(fn))
        dirname = os.path.dirname(fn)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        xr2netcdf(ds, fn)
        ds.close()

    def read_all_data(self, datasets):
        """Read Datasets from netcdf-file"""
        for dataset_name in ('params', 'matrices', 'zonal_data'):
            fn = datasets[dataset_name]
            self.read_data(dataset_name, fn)

    def read_data(self, dataset_name, fn):
        """read single dataset from """
        self.logger.info('read {}'.format(fn))
        ds = xr.open_dataset(fn)
        setattr(self, dataset_name, ds)

    def save_results(self, wiver_files):
        """Save results except trips_gsij to folder"""
        del self.results['trips_gsij']
        dataset_name = 'results'
        fn = wiver_files[dataset_name]
        self.save_data(dataset_name, fn)

    def save_results_to_visum(self, folder, visum_format='B'):
        """Save the results to VISUM-Format"""
        for m, mode in enumerate(self.modes):
            visum_ds = xr.Dataset()
            visum_ds['matrix'] = self.results.trips_mij[m]
            visum_ds['zone_no'] = self.zone_no
            visum_ds['zone_names'] = self.zone_name
            s = SavePTV(visum_ds)
            file_name = os.path.join(
                folder, '{m}_{f}.mtx'.format(m=mode, f=visum_format))
            self.logger.info('save matrix for mode {m} to {f}'.format(
                m=mode, f=file_name
            ))
            s.savePTVMatrix(file_name, Ftype=visum_format)

    def save_detailed_results_to_visum(self, folder, visum_format='B'):
        """Save the results to VISUM-Format"""
        sectors = defaultdict(list)
        for g, group in enumerate(self.groups):
            sector_id = group % 100
            sectors[sector_id].append(g)
        for sector_id, sector_groups in sectors.items():
            sector = self.params.sel(sectors=sector_id)
            name = sector.sector_name.values
            visum_ds = xr.Dataset()
            visum_ds['zone_no'] = self.zone_no
            visum_ds['zone_names'] = self.zone_name
            matrix = 0
            for g in sector_groups:
                matrix += self.results.trips_gij[g]
            visum_ds['matrix'] = matrix
            self.logger.info('Sector {s}: {t:.0f} trips'.format(
                s=sector_id, t=float(matrix.sum())
            ))
            s = SavePTV(visum_ds)
            file_name = os.path.join(
                folder, 'wiver_{sector_id}_{n}.mtx'.format(
                    sector_id=sector_id, n=name))
            self.logger.info('save matrix for sector {s}_{n} to {f}'.format(
                s=sector_id, n=name, f=file_name
            ))
            s.savePTVMatrix(file_name, Ftype=visum_format)
