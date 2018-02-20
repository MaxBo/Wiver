# -*- coding: utf-8 -*-

import multiprocessing
import os
from collections import defaultdict
import numpy as np
import pandas as pd
import xarray as xr


from cythonarrays.array_properties import _ArrayProperties
from matrixconverters.save_ptv import SavePTV
from matrixconverters.xarray2netcdf import xr2netcdf
import pyximport; pyximport.install()
from wiver.wiver_cython import (_WIVER,
                                DestinationChoiceError,
                                DataConsistencyError)

np.seterr(divide='ignore', invalid='ignore')


class WIVER(_WIVER, _ArrayProperties):
    """WIVER Commercial Trips Model"""
    _coordinates = {'n_groups': 'groups',
                    'n_modes': 'modes',
                    'n_zones': 'zone_name',
                    'n_time_slices': 'lbl_time_slice',
                    'n_sectors': 'sector_short',
                    }

    def __init__(self,
                 n_groups,
                 n_zones,
                 n_savings_categories=9,
                 n_time_slices=5,
                 n_modes=4,
                 n_sectors=2,
                 threading=True):
        super().__init__()

        self.n_modes = n_modes
        self.n_groups = n_groups
        self.n_zones = n_zones
        self.n_sectors = n_sectors
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
        self.data = xr.merge((self.params, self.matrices, self.zonal_data,
                              self.balancing))

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

        self.n_sectors = len(ds.sector_short)

        self.sector_g = ds.sector_of_groups.data
        self.mode_name = ds.mode_name.data
        self.sector_short = ds.sector_short.data
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

        self.set_arrays_from_balancing_ds(ds)

        # results
        self.results = self.define_results()

    def set_arrays_from_balancing_ds(self, ds):
        """Set arrays from balancing dataset"""
        # balancing factors
        self.balancing_factor_gj = ds.balancing_factor.data
        self.trips_to_destination_gj = ds.trips_to_destination.data

    def define_arrays(self):
        """Define the arrays"""
        self.init_object_array('groups', 'n_groups')
        self.init_object_array('group_names', 'n_groups')
        self.init_object_array('modes', 'n_modes')
        self.init_object_array('mode_name', 'n_modes')
        self.init_object_array('sector_short', 'n_sectors')
        self.init_object_array('zone_name', 'n_zones')
        self.init_object_array('lbl_time_slice', 'n_time_slices')

        self.init_array('mode_g', 'n_groups', 0)
        self.init_array('sector_g', 'n_groups', 0)
        self.init_array('active_g', 'n_groups', 1)

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
        self.init_array('balancing_factor_gj', 'n_groups, n_zones', 1)
        self.init_array('trips_to_destination_gj', 'n_groups, n_zones', 0)

        self.init_array('trips_gij', 'n_groups, n_zones, n_zones', 0)
        self.init_array('home_based_trips_gij',
                        'n_groups, n_zones, n_zones', 0)
        self.init_array('linking_trips_gij', 'n_groups, n_zones, n_zones', 0)
        self.init_array('return_trips_gij', 'n_groups, n_zones, n_zones', 0)
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
        self.balancing = self.define_balancing()
        self.results = self.define_results()

    def define_params(self):
        """Define the params"""
        ds = xr.Dataset()
        ds['modes'] = self.modes
        ds['mode_name'] = (('modes'), self.mode_name)
        ds['groups'] = self.groups
        ds['mode_of_groups'] = (('groups'),
                                self.mode_g)
        ds['sector_of_groups'] = (('groups'),
                                    self.sector_g)
        ds['sector_short'] = (('sectors'), self.sector_short)

        # assign group names
        for g in range(self.n_groups):
            self.group_names[g] = '{}_{}'.format(
                self.mode_name[self.mode_g[g]],
                self.sector_short[self.sector_g[g]])

        ds['group_names'] = (('groups'), self.group_names)

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

    def define_balancing(self):
        """Define the balancing factors"""
        ds = xr.Dataset()
        ds['balancing_factor'] = (('groups', 'destinations'),
                                    self.balancing_factor_gj)
        ds['trips_to_destination'] = (('groups', 'destinations'),
                                      self.trips_to_destination_gj)
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
                              self.matrices, self.balancing,
                              self.results))

    def save_all_data(self, wiver_files):
        """Save Dataset to netcdf-file"""
        datasets = ('params', 'zonal_data', 'matrices',
                    'balancing', 'results')
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
        for dataset_name in ('params', 'matrices', 'zonal_data' ,
                             'balancing'):
            fn = datasets[dataset_name]
            self.read_data(dataset_name, fn)

    def read_data(self, dataset_name, fn):
        """read single dataset from """
        self.logger.info('read {}'.format(fn))
        ds = xr.open_dataset(fn).load()
        ds.close()
        setattr(self, dataset_name, ds)

    def save_results(self, wiver_files):
        """Save results except trips_gsij to folder"""
        del self.results['trips_gsij']
        dataset_name = 'results'
        fn = wiver_files[dataset_name]
        self.save_data(dataset_name, fn)
        dataset_name = 'balancing'
        fn = wiver_files[dataset_name]
        self.save_data(dataset_name, fn)

    def save_results_to_visum(self, folder, visum_format='BK'):
        """Save the results to VISUM-Format"""
        for m, mode in enumerate(self.modes):
            visum_ds = xr.Dataset()
            visum_ds['matrix'] = self.results.trips_mij[m]
            visum_ds['zone_no'] = self.zone_no
            visum_ds['zone_name'] = self.zone_name
            #visum_ds['zone_names2'] = self.zone_name
            s = SavePTV(visum_ds)
            file_name = os.path.join(
                folder, '{m}.mtx'.format(m=mode))
            self.logger.info('save matrix for mode {m} to {f}'.format(
                m=mode, f=file_name
            ))
            s.savePTVMatrix(file_name, Ftype=visum_format)

    def save_detailed_results_to_visum(self, folder, visum_format='BK'):
        """Save the results to VISUM-Format"""
        sectors = defaultdict(list)
        for g, group in enumerate(self.groups):
            if self.active_g[g]:
                sector_id = group % 100
                sectors[sector_id].append(g)
        self.logger.info('sectors: {}'.format(sectors))
        for sector_id, sector_groups in sectors.items():
            self.logger.info('sector_id: {}, groups: {}'.format(sector_id,
                                                                sector_groups))
            name = self.params.sector_short.sel(sectors=sector_id).values
            self.logger.info('name: {}'.format(name))
            visum_ds = xr.Dataset()
            visum_ds['zone_no'] = self.zone_no
            visum_ds['zone_names'] = self.zone_name
            matrix = 0
            self.logger.info('Sector {s}: add wiver-groups'.format(s=sector_id))
            for g in sector_groups:
                mat = self.results.trips_gij[g]
                mode = self.mode_g[g]
                mode_descr = self.modes[mode]
                group_name = self.group_names[g]
                self.logger.info(
                    'add group {g} {m}: {s:.0f}'.format(g=group_name,
                                                        m=mode_descr,
                                                        s=float(mat.sum())))
                matrix += mat
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
            self.logger.info('matrix_saved')

    def adjust_balancing_factor(self, threshold=0.1):
        """
        Randsummenabgleich für Zielpotenziale
        """
        self.converged=False
        sp = self.zonal_data.sink_potential
        target_share = sp / sp.sum('destinations')
        trips = self.balancing.trips_to_destination
        actual_share = trips / trips.sum('destinations')
        kf = target_share / actual_share
        kf[:] = kf.fillna(1)
        bf = self.balancing.balancing_factor
        # adjust balancing factor
        bf[:] = bf.fillna(1)
        bf[:] = bf * kf
        # normalize balancing factor
        #bf[:] = bf / bf.mean('destinations')
        if (np.abs(kf - 1) < threshold).all():
            self.converged = True
            self.logger.info('converged!')

    def calc_with_balancing(self, max_iterations=10, threshold=0.1):
        """calculate with balancing the """
        self.converged = False
        iteration = 0
        while (not self.converged) and iteration < max_iterations:
            iteration += 1
            self.logger.info('calculate trips in iteration {}'.format(iteration))
            self.calc()
            self.logger.info('Total trips: {:0.2f}'.format(self.trips_gij.sum()))
            self.adjust_balancing_factor(threshold)

    def calc_starting_and_ending_trips(self):
        """
        calculate the starting trips per zone and group
        """
        trips_ij = self.results.trips_gij.sum('groups')
        modelled_trips = (trips_ij.sum('origins').\
            rename({'destinations': 'zone_no',}) + \
            trips_ij.sum('destinations').rename({'origins': 'zone_no',})) / 2

        df_modelled = modelled_trips.to_dataframe(name='modelled_trips')

        group_labels = []
        for g, group in enumerate(self.groups):
            sn = self.data.sector_short[int(self.data.sector_of_groups[g])].data
            mn = self.data.mode_name[int(self.data.mode_of_groups[g])].data
            group_label = '{}_{}'.format(mn, sn).replace(' ', '')
            group_labels.append(group_label)

        sp = self.data.sink_potential

        starting_trips_gh = (self.data.source_potential * self.data.tour_rates).\
            rename({'origins': 'zone_no',})
        ending_trips_g = starting_trips_gh.sum('zone_no') * self.data.stops_per_tour
        ending_trips_gh = sp * \
            (ending_trips_g / sp.sum('destinations'))

        starting_trips_i = starting_trips_gh.sum('groups')
        ending_trips_i = ending_trips_gh.sum('groups')

        df_balancing = self.data.balancing_factor.to_dataframe(name='balance')
        df_balancing = df_balancing.reset_index().pivot(
            index='destinations', columns='groups', values='balance')
        df_balancing.columns =['Bal_{}'.format(col)
                                  for col in group_labels]

        df_s = starting_trips_i.to_dataframe(name='starting_trips')
        df_e = ending_trips_i.to_dataframe(name='ending_trips')
        df_e.index.name = 'zone_no'
        df_modelled['start_end'] = df_s.starting_trips + df_e.ending_trips

        df_ending = ending_trips_gh.to_dataframe(name='ending_trips_g')
        df_ending = df_ending.reset_index().pivot(
            index='destinations', columns='groups', values='ending_trips_g')

        df_ending.index.name = 'zone_no'
        df_ending.columns =['End_{}'.format(col)
                                for col in group_labels]

        df_starting = starting_trips_gh.to_dataframe(name='starting_trips_g')
        df_starting = df_starting.reset_index().pivot(
            index='zone_no', columns='groups', values='starting_trips_g')
        df_starting.columns =['Start_{}'.format(col)
                                for col in group_labels]

        df_sp = self.data.sink_potential.to_dataframe(name='sink_potential')
        df_sp = df_sp.reset_index().\
            rename(columns={'destinations': 'zone_no',}).\
            pivot(index='zone_no', columns='groups', values='sink_potential')
        df_sp.columns =['SP_{}'.format(col)
                        for col in group_labels]

        df_name = self.data.zone_name.to_dataframe()

        df = pd.concat([df_name,
                        df_modelled,
                        df_s,
                        df_e,
                        df_starting,
                        df_ending,
                        df_sp,
                        df_balancing],
                       axis=1)
        return df

