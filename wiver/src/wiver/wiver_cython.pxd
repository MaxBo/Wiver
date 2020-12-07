# -*- coding: utf-8 -*-

from cythonarrays.numpy_types cimport *

from cythonarrays.array_shapes cimport ArrayShapes
from cythonarrays.array_shapes import ArrayShapes


cdef class _WIVER(ArrayShapes):
    """
    BaseClass for WIVER model
    with n_groups and n_zones
    """
    cdef public long32 n_groups
    cdef public long32 n_zones
    cdef public char n_threads
    cdef public char n_savings_categories
    cdef public char n_time_slices
    cdef public char n_modes
    cdef public char n_sectors

    # Zone-number
    cdef public ARRAY_1D_i8 _zone_no

    # mode and sector of groups
    cdef public ARRAY_1D_i1 _mode_g
    cdef public ARRAY_1D_i1 _sector_g

    # active groups
    cdef public ARRAY_1D_i1 _active_g

    # Savings bins and weights for each group
    cdef public ARRAY_1D_d _savings_bins_s
    cdef public ARRAY_2D_d _savings_weights_gs

    # distance matrix (km from a to b)
    cdef public ARRAY_2D_d _km_ij

    # skim matrix (travel time from a to b)
    cdef public ARRAY_3D_d _travel_time_mij

    # Distance Parameter for each group
    cdef public ARRAY_1D_d _param_dist_g

    # Mean Distance for each group
    cdef public ARRAY_1D_d _mean_distance_g
    # Mean Distance for each mode
    cdef public ARRAY_1D_d _mean_distance_m

    # Tour rates and number of stops per tour by group
    cdef public ARRAY_1D_d _tour_rates_g
    cdef public ARRAY_1D_d _stops_per_tour_g

    # Sources and Sinks for each group
    cdef public ARRAY_2D_d _source_potential_gh
    cdef public ARRAY_2D_d _sink_potential_gj
    cdef public ARRAY_2D_d _balancing_factor_gj

    # time series for each group
    cdef public ARRAY_2D_d _time_series_starting_trips_gs
    cdef public ARRAY_2D_d _time_series_linking_trips_gs
    cdef public ARRAY_2D_d _time_series_ending_trips_gs

    # resulting trips
    cdef public ARRAY_3D_d _trips_gij
    cdef public ARRAY_3D_d _home_based_trips_gij
    cdef public ARRAY_3D_d _linking_trips_gij
    cdef public ARRAY_3D_d _return_trips_gij

    cdef public ARRAY_2D_d _trips_to_destination_gj

    # Trips by time slice
    cdef public ARRAY_4D_d _trips_gsij

    # trips_by_mode
    cdef public ARRAY_3D_d _trips_mij
    cdef public ARRAY_4D_d _trips_msij

    # internal probability matrices for each thread
    cdef public ARRAY_3D_d _p_destination_tij
    cdef public ARRAY_3D_d _p_links_tij

    cpdef char calc_daily_trips(self) except -1
    cdef double _calc_tours(self, long32 g, long32 h) nogil
    cdef double _calc_linking_trips(self, long32 g, double tours) nogil
    cdef double _calc_p_destination(self, long32 g, char m,
                                    long32 h, long32 j) nogil
    cdef char _calc_destination_choice(self,
                                      char t,
                                      long32 g,
                                      long32 h) nogil

    cdef char _calc_linking_trip_choice(self,
                                      char t,
                                      long32 g,
                                      long32 h) nogil

    cdef char _symmetrisize_trip_matrix(self, long32 g,) nogil

    cdef char _calc_trips(self,
                         char t,
                         long32 g,
                         long32 h,
                         double tours,
                         double linking_trips) nogil
    cdef double _calc_savings_factor(self, long32 g, char m,
                                   long32 h, long32 i, long32 j) nogil
    cdef double _calc_savings(self, long32 g, char m,
                             long32 h, long32 i, long32 j) nogil

    cpdef calc_time_series(self)
    cpdef aggregate_to_modes(self)
    cpdef calc_mean_distance(self)
    cpdef calc_mean_distance_mode(self)