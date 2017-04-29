# -*- coding: utf-8 -*-

import os
import orca


@orca.injectable()
def dataset_fn():
    fn = os.path.join(os.path.dirname(__file__),
                      'example_dataset.h5')
    return fn


@orca.injectable()
def zones_fn():
    fn = os.path.join(os.path.dirname(__file__),
                      'zones.h5')
    return fn
