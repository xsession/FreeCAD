# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Mesher and solver adapter implementations."""

from .base import BaseSolverAdapter
from .elmer import ElmerSolverAdapter
from .geant4 import Geant4SolverAdapter
from .openfoam import OpenFOAMSolverAdapter

try:
    from .fluidx3d import FluidX3DOptionalAdapter
except Exception:  # pragma: no cover - optional adapter may be unavailable
    FluidX3DOptionalAdapter = None

__all__ = [
    "BaseSolverAdapter",
    "ElmerSolverAdapter",
    "FluidX3DOptionalAdapter",
    "Geant4SolverAdapter",
    "OpenFOAMSolverAdapter",
]
