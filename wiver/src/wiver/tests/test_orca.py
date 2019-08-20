# -*- coding: utf-8 -*-
"""
Created on Fri Jun 10 21:00:21 2016

@author: MaxBohnet
"""

import os
import orca
import pytest
import wiver.run_wiver


class Test01_Run_Orca:
    """Test export results"""
    def test_10_get_result_path(self):
        orca.injectables['project_folder'] = 'FilePath_with_ÄÖÜß'
        with pytest.raises(orca.OrcaError):
            orca.get_injectable('starting_ending_trips_file')

        orca.injectables['project_folder'] = 'FilePath_only_ASCII'
        inj = orca.get_injectable('starting_ending_trips_file')

