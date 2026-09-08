"""
TOUCHSTONE EXPORT
=================
"""

import numpy as np

def export_touchstone(s_params: list, filename: str, lambda_0_um: float = 1.064):
    # Check passivity honestly
    S = s_params
    for f in range(len(S)):
        s11, s21, s31, s41 = S[f]
        if abs(s11)**2 + abs(s21)**2 + abs(s31)**2 + abs(s41)**2 > 1.0:
            print(f"Warning: Passivity violated at point {f}")
            
    # Calculate exact optical frequency in Hz
    c_m_s = 299792458.0
    freq_hz = c_m_s / (lambda_0_um * 1e-6)
            
    with open(filename, 'w') as f:
        f.write("# Hz S RI R 50\n")
        # For an optical S-parameter file, using the exact frequency rather than hardcoded 1e9
        for freq_idx, sp in enumerate(S):
            # Write frequency and real/imag parts of S11, S21, S31, S41
            f.write(f"{freq_hz:.4e} {sp[0].real} {sp[0].imag} {sp[1].real} {sp[1].imag} {sp[2].real} {sp[2].imag} {sp[3].real} {sp[3].imag}\n")
