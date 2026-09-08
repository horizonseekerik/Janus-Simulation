"""
Tier 2 Thermal Modeling
=======================
Genuine computational thermal physics pipeline for Project Janus (Architecture C):
- Elmer3DThermalPipeline: True 3D Elmer FEM thermal simulation pipeline. Executes ElmerGrid
  and ElmerSolver via subprocess on conforming Gmsh tetrahedral meshes, solving the 3D steady-state
  heat equation and parsing scalars.dat and line.dat. Falls back to 1D finite-volume solver if Elmer is uninstalled.
- TransientThermal1D: 1D multi-stratum finite-volume / method-of-lines solver with harmonic-mean
  conductances across layer boundaries. Used for spatial grid convergence studies and independent
  analytical resistance benchmarking.
- Gmsh3DMeshGenerator: 3D macro package mesh generator utilizing simultaneous OpenCASCADE boolean
  fragmentation for 100% conforming interface nodes (zero duplicate surfaces).
- NanoscaleCellThermalSubmodel: Compact thermal RC submodel for localized spreading and thin-film
  conduction across the 1 nm graphene heater and 15 nm Sb2S3 PCM cell (tau_nano ~ 1.29 ns).
- ThermalROMExtractor: Fits a 5-pole Foster RC state-space network to the computed step response (R^2 >= 0.999).
"""

from tier2_elmer_thermal.elmer_thermal_solver import (
    Elmer3DThermalPipeline,
    TransientThermal1D,
    NanoscaleCellThermalSubmodel,
    ThermalFEMSolver,
    Thermal3DStackSolver,
    Thermal1DStackSolver,
)
from tier2_elmer_thermal.gmsh_mesh_generator import Gmsh3DMeshGenerator
from tier2_elmer_thermal.extract_thermal_rom import ThermalROMExtractor

__all__ = [
    "Elmer3DThermalPipeline",
    "TransientThermal1D",
    "NanoscaleCellThermalSubmodel",
    "ThermalFEMSolver",
    "Thermal3DStackSolver",
    "Thermal1DStackSolver",
    "Gmsh3DMeshGenerator",
    "ThermalROMExtractor",
]

