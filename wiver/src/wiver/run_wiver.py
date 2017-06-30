# -*- coding: utf-8 -*-
"""
Created on Fri Jun 10 21:00:21 2016

@author: MaxBohnet
"""

import tempfile
import os
from argparse import ArgumentParser
from typing import List
import numpy as np
import orca
from wiver.wiver_python import WIVER
from cythonarrays.configure_logger import SimLogger


@orca.injectable()
def project_folder():
    """ The Project folder (%TEMP% by default)"""
    folder = tempfile.gettempdir()
    return folder


@orca.injectable()
def params_file(project_folder):
    """ The params-file"""
    fn = 'params'
    file_path = os.path.join(project_folder, '{}.h5'.format(fn))
    return file_path


@orca.injectable()
def matrix_file(project_folder):
    """ The params-file"""
    fn = 'matrices'
    file_path = os.path.join(project_folder, '{}.h5'.format(fn))
    return file_path


@orca.injectable()
def zones_file(project_folder):
    """ The zonal_data-file"""
    fn = 'zonal_data'
    file_path = os.path.join(project_folder, '{}.h5'.format(fn))
    return file_path


@orca.injectable()
def result_file(project_folder):
    """ The results-file"""
    fn = 'results'
    file_path = os.path.join(project_folder, '{}.h5'.format(fn))
    return file_path


@orca.injectable()
def balancing_file(project_folder):
    """ The balancing-file"""
    fn = 'balancing'
    file_path = os.path.join(project_folder, '{}.h5'.format(fn))
    return file_path


@orca.injectable()
def max_iterations():
    """ maximum number of iterations"""
    return 1


@orca.injectable()
def wiver_files(params_file, matrix_file, zones_file,
                balancing_file, result_file):
    files = {'params': params_file,
             'matrices': matrix_file,
             'zonal_data': zones_file,
             'balancing': balancing_file,
             'results': result_file}
    return files


@orca.injectable()
def wiver(wiver_files):
    wiver = WIVER.read_from_netcdf(wiver_files)
    return wiver


@orca.injectable()
def scenario():
    """The Scenario Name"""
    return 'wiver'


@orca.step()
def add_logfile(project_folder: str, scenario: str):
    """
    add Logfile to logger

    Parameters
    ---------
    wiver model
    """
    logger = SimLogger()
    logger.add_packages(['wiver'])
    logfile = os.path.join(project_folder, 'log')
    logger.configure(logfile, scenario=scenario)

@orca.step()
def run_wiver(wiver: WIVER, wiver_files: dict, max_iterations: int):
    """
    calculate wiver model

    Parameters
    ---------
    wiver: wiver-model
    wiver-files : dict
    max_iterations: int
    """
    wiver.calc_with_balancing(max_iterations=max_iterations)
    wiver.save_results(wiver_files)

@orca.step()
def run_wiver_for_selected_groups(wiver: WIVER,
                                  wiver_files: dict,
                                  max_iterations: int,
                                  groups_to_calculate: List[int]):
    """
    calculate wiver model for selected groups only

    Parameters
    ---------
    wiver: wiver-model
    wiver-files : dict
    max_iterations: int
    groups_to_calculate: list of int
    """
    if groups_to_calculate:
        wiver.active_g[:] = np.in1d(wiver.groups, groups_to_calculate)
    wiver.calc_with_balancing(max_iterations=max_iterations)
    wiver.save_results(wiver_files)

@orca.step()
def save_results(wiver: WIVER, wiver_files: dict, matrix_folder: str):
    """
    save result matrices of wiver-model

    Parameters
    ----------
    wiver: wiver-model
    wiver-files : dict
    matrix_folder: str
        the folder to store the calculated matrices
    """
    fn = wiver_files['results']
    wiver.read_data('results', fn)
    wiver.save_results_to_visum(matrix_folder, 'B')


@orca.step()
def save_detailed_results(wiver: WIVER,
                          wiver_files: dict,
                          matrix_folder: str):
    """
    save detailed result matrices of wiver-model

    Parameters
    ----------
    wiver: wiver-model
    wiver-files : dict
    matrix_folder: str
        the folder to store the calculated matrices
    """
    fn = wiver_files['results']
    wiver.read_data('results', fn)
    wiver.save_detailed_results_to_visum(matrix_folder, 'B')


if __name__ == '__main__':
    parser = ArgumentParser(description="Commercial Trip Model Wiver")
    parser.add_argument('-f', '--folder', dest='project_folder',
                        help='Project folder',
                        required=True)
    parser.add_argument('-m', '--matrix-folder', dest='matrix_folder',
                        help='Matrix folder',
                        required=True)
    parser.add_argument('-s', '--scenario', dest='scenario',
                        help='Scenario Name', default='Wiver',)
    parser.add_argument('-i', '--iterations', dest='max_iterations',
                        help='Maximum number of iterations', type=int,
                        default=5,)
    parser.add_argument('-g', '--groups', dest='groups_to_calculate',
                        help='groups to calculate', type=int, nargs='+')

    options = parser.parse_args()
    for key, value in options._get_kwargs():
        orca.add_injectable(key, value)

    orca.run([
        'add_logfile',
        #'run_wiver',
        'run_wiver_for_selected_groups',
        'save_results',
        #'save_detailed_results',
        ])
