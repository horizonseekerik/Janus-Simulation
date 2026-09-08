"""
EXPORT HEAT MAP
===============
"""

import numpy as np

def export_heatmap(e_field, n_imag, filename):
    # e_field from sim.get_array()
    abs_field = np.abs(e_field)**2
    absorption = abs_field * n_imag
    np.save(filename, absorption)
