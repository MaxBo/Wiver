# -*- coding: utf-8 -*-
"""
Created on Fri Jun 10 21:00:21 2016

@author: MaxBohnet
"""

import os
import orca
import tempfile
from argparse import ArgumentParser
from wiver.wiver_python import (WIVER)
from wiver.wiver_xml_param_parser import XMLParamParser
from wiver.wiver import (project_folder,
                         params_file,
                         matrix_file,
                         zones_file,
                         result_file,
                         wiver,
                         run_wiver,
                         save_results,
                         )


def main():
    parser = ArgumentParser(description="Travel Demand Model")

    parser.add_argument("-xml", action="store",
                        help="XML parameter file",
                        dest="xml_params", default=None)

    parser.add_argument("-n", action="store",
                        help="Scenario Name",
                        dest="scenario_name", default='BaseScenario')

    parser.add_argument("-r", action="store",
                        help="name of the run",
                        dest="run_name", default='Gesamtlauf')

    options = parser.parse_args()

    x = XMLParamParser(options.xml_params,
                       options.scenario_name,
                       options.run_name)

    for key in x:
        value = x[key]
        if value is not None:
            orca.add_injectable(key, value)

    orca.run(['run_wiver', 'save_results'])


if __name__ == '__main__':
    main()
