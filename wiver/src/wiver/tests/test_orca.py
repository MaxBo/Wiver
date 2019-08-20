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
    def test_10_result_path_with_non_ascii_characters(self):
        injectables = orca.orca._INJECTABLES
        injectables['project_folder'] = 'FilePath_with_ÄÖÜß'

        with pytest.raises(orca.OrcaError,
                           match='contains non-ascii-characters$') as e:
            orca.get_injectable('result_file')

        dirname = 'FilePath_only_ASCII'
        injectables['project_folder'] = dirname
        inj = orca.get_injectable('result_file')
        assert(inj == os.path.join(dirname, 'results.h5'))

