# -*- coding: utf-8 -*-
#cython: boundscheck=False
#cython: wraparound=False
#cython: cdivision=True
#cython: embedsignature=True

cimport cython
cimport numpy as np
import numpy as np

from cython.parallel import prange, threadid, parallel
cimport openmp
from cythonarrays.numpy_types cimport *
from cythonarrays.array_properties import _ArrayProperties
from cythonarrays.array_shapes cimport ArrayShapes
from cythonarrays.array_shapes import ArrayShapes

from libc.math cimport exp, log


class DestinationChoiceError(ValueError):
    """
    Error in destination choice model,
    no accessible destinations found for demand
    """

class DataConsistencyError(IndexError):
    """
    Data is not consistent and could lead to IndexErrors when running the model
    with these data
    """


cdef class _WIVER(ArrayShapes):
    """
    BaseClass for WIVER model
    with n_groups and n_zones
    """

    @cython.initializedcheck(False)
    cpdef char calc_daily_trips(self) except -1:
        """
        Calc the daily trips for all groups and zones

        Returns
        -------
        int:
            -1, if an exeption is raised, 0 otherwise
        """
        cdef char t, r
        cdef long32 g, h
        cdef double tours, linking_trips
        self.reset_array('home_based_trips_gij')
        self.reset_array('linking_trips_gij')
        with nogil, parallel(num_threads=self.n_threads):
            t = threadid()
            # loop over calibration groups
            for g in prange(self.n_groups, schedule='guided'):
                if not self._active_g[g]:
                    continue
                with gil:
                    mode = self._mode_g[g]
                    sector = self._sector_g[g]
                    name = '{}_{}'.format(self.mode_name[mode],
                                          self.sector_short[sector])
                    self.logger.info('calculate group {} ({})'.format(g, name))
                # loop over home zones
                for h in range(self.n_zones):
                    tours = self._calc_tours(g, h)
                    if tours:
                        r = self._calc_destination_choice(t, g, h)
                        if r:
                            with gil:
                                self.raise_destination_choice_error(g, h)
                        linking_trips = self._calc_linking_trips(g, tours)
                        if linking_trips:
                            r = self._calc_linking_trip_choice(t, g, h)
                            if r:
                                with gil:
                                    self.raise_linking_trips_error(g, h)
                        self._calc_trips(t, g, h, tours, linking_trips)
                self._symmetrisize_trip_matrix(g)
        self.trips_gij[:] = (self.home_based_trips_gij +
                            self.linking_trips_gij +
                            self.return_trips_gij)
        self.trips_to_destination_gj[:] = (self.home_based_trips_gij +
                                           self.linking_trips_gij).sum(1)

    def raise_destination_choice_error(self, g, h):
        """raise a DestinationChoiceError for destination trips"""
        msg = '''No accessible destinations found for group {g} and home zone {h}'''
        raise DestinationChoiceError(msg.format(g=g, h=h))

    def raise_linking_trips_error(self, g, h):
        """raise a DestinationChoiceError for linking trips"""
        msg = '''No destinations cannot be linked for group {g} and home zone {h} because they is no accessibility between the destinations'''
        raise DestinationChoiceError(msg.format(g=g, h=h))

    def calc(self):
        """calc the daily trips and the trips by time slice"""
        self.calc_daily_trips()
        self.calc_time_series()
        self.aggregate_to_modes()
        self.calc_mean_distance()
        self.calc_mean_distance_mode()

    @cython.initializedcheck(False)
    cpdef calc_mean_distance(self):
        """calculate mean distance for groups"""
        cdef long32 g, i, j, mode, sector
        cdef double total_distance, total_trips,
        cdef double trips, home_based_trips, mean_distance
        cdef double total_distance_first_trip, total_tours,
        cdef double mean_distance_first_trip
        cdef double mean_distance_linking_trip
        cdef double total_linking_trips
        cdef double linking_trips
        cdef double total_distance_linking_trips

        for g in range(self.n_groups):
            if not self._active_g[g]:
                self._mean_distance_g[g] = self.NAN_d
                continue
            mode = self._mode_g[g]
            sector = self._sector_g[g]
            name = '{}_{}'.format(self.mode_name[mode],
                                  self.sector_short[sector])
            total_distance = 0
            total_distance_first_trip = 0
            total_distance_linking_trips = 0
            total_trips = 0
            total_linking_trips = 0
            total_tours = 0
            # loop over zones
            for i in range(self.n_zones):
                for j in range(self.n_zones):
                    trips = self._trips_gij[g, i, j]
                    home_based_trips = self._home_based_trips_gij[g, i, j]
                    linking_trips = self._linking_trips_gij[g, i, j]

                    total_distance += self._km_ij[i, j] * trips
                    total_distance_first_trip += (self._km_ij[i, j] *
                                                  home_based_trips)
                    total_distance_linking_trips += (self._km_ij[i, j] *
                                                     linking_trips)

                    total_trips += trips
                    total_tours += home_based_trips
                    total_linking_trips += linking_trips

            mean_distance = total_distance / total_trips
            mean_distance_first_trip = total_distance_first_trip / total_tours
            mean_distance_linking_trip = total_distance_linking_trips / total_linking_trips

            self.logger.info('mean distance of group {n:15} ({g:3}): '\
                '{d:5.2f} km, {t:7.0f} trips, {td:7.0f} vkm. '\
                'HomeBased: {dh:5.2f} km, {th:7.0f} trips, {tdh:7.0f} vkm. '\
                'LinkingTrips: {dl:5.2f} km, {tl:7.0f} trips, {tdl:7.0f} vkm. '.\
                format(g=g, n=name, d=mean_distance, t=total_trips,
                td=total_distance, dh=mean_distance_first_trip,
                th=total_tours, tdh=total_distance_first_trip,
                tl=total_linking_trips, tdl=total_distance_linking_trips,
                dl=mean_distance_linking_trip))
            self._mean_distance_g[g] = mean_distance


    @cython.initializedcheck(False)
    cpdef calc_mean_distance_mode(self):
        """calculate mean distance for modes"""
        cdef long32 m, i, j
        cdef double total_distance, total_trips, trips, mean_distance
        for m in range(self.n_modes):
            name = self.mode_name[m]
            total_distance = 0
            total_trips = 0
            # loop over zones
            for i in range(self.n_zones):
                for j in range(self.n_zones):
                    trips = self._trips_mij[m, i, j]
                    total_distance += self._km_ij[i, j] * trips
                    total_trips += trips
            mean_distance = total_distance / total_trips
            self.logger.info('mean distance of mode {m} ({n}): {d:0.2f}'.\
                format(m=m, n=name, d=mean_distance))
            self._mean_distance_m[m] = mean_distance

    @cython.initializedcheck(False)
    cdef double _calc_tours(self, long32 g, long32 h) nogil:
        """
        calc the number of linking trips starting in home zone h
        """
        cdef double tours
        tours = self._source_potential_gh[g, h] * self._tour_rates_g[g]
        return tours

    @cython.initializedcheck(False)
    cdef double _calc_linking_trips(self, long32 g, double tours) nogil:
        """
        calc the number of linking trips for group g
        """
        cdef double linking_trips
        linking_trips = tours * (self._stops_per_tour_g[g] - 1)
        return linking_trips

    @cython.initializedcheck(False)
    cdef double _calc_p_destination(self, long32 g, char m,
                                    long32 h, long32 j) nogil:
        """
        calc utility function for the destination choice
        """
        cdef double p
        cdef double sp = self._sink_potential_gj[g, j]
        cdef double bf = self._balancing_factor_gj[g, j]
        cdef double param = self._param_dist_g[g]
        cdef double time = self._travel_time_mij[m, h, j]
        p = sp * bf * exp(param * time)
        return p

    @cython.initializedcheck(False)
    cdef char _calc_destination_choice(self,
                                      char t,
                                      long32 g,
                                      long32 h) nogil:
        """
        calc the Destination choice

        Parameters
        ----------
        t : char
            the thread_no
        g : long32
            group no
        h : long 32
            home zone no

        Returns
        -------
        r : char
            error code, if -1 this should raise a DestinationChoiceError
        """
        cdef double p, total_weights
        cdef long32 j
        cdef char m = self._mode_g[g]

        # destination choice probability
        total_weights = 0
        for j in range(self.n_zones):
            p = self._calc_p_destination(g, m, h, j)
            self._p_destination_tij[t, h, j] = p
            total_weights += p
        if not total_weights:
            return -1
        for j in range(self.n_zones):
            self._p_destination_tij[t, h, j] /= total_weights
        return 0

    @cython.initializedcheck(False)
    cdef char _calc_linking_trip_choice(self,
                                      char t,
                                      long32 g,
                                      long32 h) nogil:
        """
        calc the Distribution for the linking trips

        Parameters
        ----------
        t : char
            the thread_no
        g : long32
            group no
        h : long 32
            home zone no

        Returns
        -------
        r : char
            error code, if -1 this should raise a DestinationChoiceError
        """
        cdef char m = self._mode_g[g]
        cdef long32 i, j
        cdef double p, pi, pj, total_weights, savings_factor

        # reset arrays
        #self._weight_links_total_t[t] = 0
        total_weights = 0
        with gil:
            self.p_links_tij[t] = 0

        # tour generation for linking trips
        # loop over destinations
        for i in range(self.n_zones):
            pi = self._p_destination_tij[t, h, i]
            if pi:
                for j in range(self.n_zones):
                    pj = self._p_destination_tij[t, h, j]
                    if pj:
                        savings_factor = self._calc_savings_factor(
                        g, m, h, i, j)
                        p = pi * pj * savings_factor
                        self._p_links_tij[t, i, j] = p
                        total_weights += p

        if not total_weights:
            return -1
        for i in range(self.n_zones):
            for j in range(self.n_zones):
                self._p_links_tij[t, i, j] /= total_weights
        return 0

    @cython.initializedcheck(False)
    cdef char _calc_trips(self,
                         char t,
                         long32 g,
                         long32 h,
                         double tours,
                         double linking_trips) nogil:

        cdef long32 i, j
        cdef double trips, p
        # Fahrten Heimatzone - 1. Stop-Heimatzone
        for i in range(self.n_zones):
            trips = tours * self._p_destination_tij[t, h, i]
            self._home_based_trips_gij[g, h, i] += trips

            if linking_trips:
                # Zwischenfahrten
                for j in range(self.n_zones):
                    p = self._p_links_tij[t, i, j]
                    if p:
                        trips = linking_trips * p
                        self._linking_trips_gij[g, i, j] += trips

    @cython.initializedcheck(False)
    cdef double _calc_savings_factor(self, long32 g, char m,
                                    long32 h, long32 i, long32 j) nogil:
        """Calc the saving factor"""

        cdef double savings, savings_factor
        cdef char s
        savings = self._calc_savings(g, m, h, i, j)
        for s in range(self.n_savings_categories):
            if savings <= self._savings_bins_s[s]:
                break
        savings_factor = self._savings_weights_gs[g, s]
        return savings_factor

    @cython.initializedcheck(False)
    cdef double _calc_savings(self, long32 g, char m,
                              long32 h, long32 i, long32 j) nogil:
        """Calc the savings"""
        cdef double savings, t_hi ,t_jh, t_ij

        t_hi = self._travel_time_mij[m, h, i]
        t_jh = self._travel_time_mij[m, j, h]
        t_ij = self._travel_time_mij[m, i, j]
        savings = (t_hi + t_jh - t_ij) / (t_hi + t_jh)
        return savings

    @cython.initializedcheck(False)
    cdef char _symmetrisize_trip_matrix(self, long32 g,) nogil:
        """
        Symmetrisize the linking trips matrix and
        Calculate the trips back home
        """
        cdef long i, j
        cdef double t1, t2, t0
        for i in range(self.n_zones):
            for j in range(self.n_zones):

                # calculate the mean of forward and backward trips
                t1 = self._linking_trips_gij[g, i, j]
                t2 = self._linking_trips_gij[g, j, i]
                t0 = (t1 + t2) / 2
                self._linking_trips_gij[g, i, j] = t0
                self._linking_trips_gij[g, j, i] = t0

                # set the return trips
                self._return_trips_gij[g, i, j] = \
                    self._home_based_trips_gij[g, j, i]


    # python wrapper functions around nogil-functions - for testing purposes
    def calc_savings(self, g, m, h, i, j):
        """
        calc the savings for group g with home zone h from zone i to j
        """
        return self._calc_savings(g, m, h, i, j)

    def calc_savings_factor(self, g, m, h, i, j):
        """
        calc the saving factor for group g with home zone h from zone i to j
        """
        return self._calc_savings_factor(g, m, h, i, j)

    def calc_tours(self, g, h):
        return self._calc_tours(g, h)

    def calc_linking_trips(self, g, tours):
        return self._calc_linking_trips(g, tours)

    def calc_p_destination(self, g, m, h, j):
        return self._calc_p_destination(g, m, h, j)

    def calc_destination_choice(self, t, g, h):
        r = self._calc_destination_choice(t, g, h)
        if r:
            self.raise_destination_choice_error(g, h)

    def calc_linking_trip_choice(self, t, g, h):
        r = self._calc_linking_trip_choice(t, g, h)
        if r:
            self.raise_linking_trips_error(g, h)

    def calc_trips(self, t, g, h, tours, linking_trips):
        return self._calc_trips(t, g, h, tours, linking_trips)

    def normalise_time_series(self, np.ndarray time_series):
        """normalise a time_series to ensure it adds up to 100 %"""
        time_series /= time_series.sum(-1)[:, np.newaxis]

    @cython.initializedcheck(False)
    cpdef calc_time_series(self):
        """Calc the time series"""
        self.assert_data_consistency()
        cdef long32 g, s, i, j
        cdef double trips, w_starting, w_linking, w_ending
        self.reset_array('trips_gsij')
        # normalize the weights to ensure that all time slices sum up to 100 %
        self.normalise_time_series(self.time_series_starting_trips_gs)
        self.normalise_time_series(self.time_series_linking_trips_gs)
        self.normalise_time_series(self.time_series_ending_trips_gs)

        # loop over all groups
        with nogil, parallel(num_threads=self.n_threads):
            for g in prange(self.n_groups):
                for s in range(self.n_time_slices):
                    w_starting = self._time_series_starting_trips_gs[g, s]
                    w_linking = self._time_series_linking_trips_gs[g, s]
                    w_ending = self._time_series_ending_trips_gs[g, s]
                    for i in range(self.n_zones):
                        for j in range(self.n_zones):
                            trips = (
                            self._home_based_trips_gij[g, i, j] * w_starting +
                            self._linking_trips_gij[g, i, j] * w_linking +
                            self._return_trips_gij[g, i, j] * w_ending)

                            self._trips_gsij[g, s, i, j] = trips

    @cython.initializedcheck(False)
    cpdef aggregate_to_modes(self):
        """Aggregate result matrices to mode-matrices"""
        cdef long32 g, i, j, m, s
        cdef double trips
        # reset the result arrays
        self.reset_array('trips_mij')
        self.reset_array('trips_msij')

        # loop over groups
        for g in range(self.n_groups):
            m = self._mode_g[g]
            for i in range(self.n_zones):
                for j in range(self.n_zones):
                    # add to daily matrix
                    trips = self._trips_gij[g, i, j]
                    self._trips_mij[m, i, j] += trips
                    # add to time-slice matrix
                    for s in range(self.n_time_slices):
                        trips = self._trips_gsij[g, s, i, j]
                        self._trips_msij[m, s, i, j] += trips


    def assert_data_consistency(self):
        """assert the data consistency"""
        self.assert_data_consistency_of_array('mode_g', 'n_modes')

    def assert_data_consistency_of_array(self, str attrname, str dim):
        """
        assert the consistency of array attrname

        Parameters
        ----------
        attrname:
            the name of the attribute to test
        dim:
            the name of the dimension to test
        """
        # modes of groups
        lbound = 0
        ubound = getattr(self, dim)
        arr = getattr(self, attrname)
        a = np.logical_or(arr < lbound, arr >= ubound)
        if a.any():
            msg = '''array {v} should only contain values v with 0 <= v < {d}={n},
but contains the following invalid values at pos {pos}:
{val}'''
            raise DataConsistencyError(msg.format(v=attrname, d=dim, n=ubound,
            pos=a.nonzero(), val=arr[a]))
