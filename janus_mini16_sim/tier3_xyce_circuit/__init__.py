"""
PROJECT JANUS MINI (16-TILE): TIER 3 CIRCUIT & SIGNAL INTEGRITY PACKAGE
=======================================================================
Analytical circuit and signal integrity models:
- Algorithm 3A: S-Parameter Vector Fitting & SPICE Exporter (vector_fit_s_params.py)
- Algorithm 3B: APD Receiver Analytical Model (apd_receiver_model.py)
- Algorithm 3C: StrongARM Latch Model (strongarm_latch.py)
- Algorithm 3D & 3E: Eye Diagram & BER Solver (eye_diagram_ber.py)
- Algorithm 3F: ILO Comb Lock Model (ilo_comb_lock.py)
"""

from .vector_fit_s_params import VectorFitSParams
from .apd_receiver_model import APDReceiverAnalytical
from .strongarm_latch import StrongArmLatchModel
from .eye_diagram_ber import EyeDiagramAndBERSolver
from .ilo_comb_lock import ILOCombLockModel

__all__ = [
    "VectorFitSParams",
    "APDReceiverAnalytical",
    "StrongArmLatchModel",
    "EyeDiagramAndBERSolver",
    "ILOCombLockModel",
]

__version__ = "1.0.0"
__tier__ = "Tier 3: Xyce Circuit & Signal Integrity"
