# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Generic FloEFD-style task panel for non-CFD boundary conditions."""

from PySide import QtGui

from flow_studio.taskpanels.task_flowefd_features import FloEFDTaskPanel
from flow_studio.ui.generic_bc_presenter import GenericBoundaryPresenter, GenericBoundarySettings


BC_FIELDS = {
    "FlowStudio::BCFixedDisplacement": [
        ("FixX", "Fix X"),
        ("FixY", "Fix Y"),
        ("FixZ", "Fix Z"),
        ("DisplacementX", "Displacement X [m]"),
        ("DisplacementY", "Displacement Y [m]"),
        ("DisplacementZ", "Displacement Z [m]"),
    ],
    "FlowStudio::BCForce": [
        ("ForceX", "Force X [N]"),
        ("ForceY", "Force Y [N]"),
        ("ForceZ", "Force Z [N]"),
    ],
    "FlowStudio::BCPressureLoad": [("Pressure", "Pressure [Pa]")],
    "FlowStudio::BCTemperature": [("Temperature", "Temperature [K]")],
    "FlowStudio::BCHeatFlux": [("HeatFlux", "Heat flux [W/m^2]")],
    "FlowStudio::BCConvection": [
        ("HeatTransferCoefficient", "Heat transfer coefficient [W/(m^2 K)]"),
        ("AmbientTemperature", "Ambient temperature [K]"),
    ],
    "FlowStudio::BCRadiation": [
        ("Emissivity", "Emissivity [-]"),
        ("AmbientTemperature", "Ambient temperature [K]"),
    ],
    "FlowStudio::BCElectricPotential": [
        ("Potential", "Potential [V]"),
        ("CalculateForce", "Calculate force"),
    ],
    "FlowStudio::BCSurfaceCharge": [("SurfaceChargeDensity", "Surface charge density [C/m^2]")],
    "FlowStudio::BCElectricFlux": [("FluxDensity", "Electric flux density [C/m^2]")],
    "FlowStudio::BCMagneticPotential": [
        ("MagneticVectorPotential", "Magnetic vector potential [Wb/m]"),
        ("ZeroPotential", "Zero potential"),
    ],
    "FlowStudio::BCCurrentDensity": [
        ("CurrentDensityX", "Current density X [A/m^2]"),
        ("CurrentDensityY", "Current density Y [A/m^2]"),
        ("CurrentDensityZ", "Current density Z [A/m^2]"),
    ],
    "FlowStudio::BCMagneticFluxDensity": [
        ("FluxDensityX", "Flux density X [T]"),
        ("FluxDensityY", "Flux density Y [T]"),
        ("FluxDensityZ", "Flux density Z [T]"),
    ],
    "FlowStudio::BCFarFieldEM": [("UseZeroPotential", "Use zero potential")],
    "FlowStudio::BCOpticalSource": [
        ("SourceType", "Source type"),
        ("Power", "Power [W]"),
        ("Wavelength", "Wavelength [nm]"),
        ("BeamRadius", "Beam radius [mm]"),
        ("DivergenceAngle", "Divergence angle [deg]"),
        ("RayCount", "Ray count"),
    ],
    "FlowStudio::BCOpticalDetector": [
        ("DetectorType", "Detector type"),
        ("PixelsX", "Pixels X"),
        ("PixelsY", "Pixels Y"),
        ("Width", "Width [mm]"),
        ("Height", "Height [mm]"),
    ],
    "FlowStudio::BCOpticalBoundary": [
        ("BoundaryType", "Boundary type"),
        ("Reflectivity", "Reflectivity [-]"),
        ("Transmission", "Transmission [-]"),
        ("Scatter", "Scatter [-]"),
    ],
    "FlowStudio::BCGeant4Source": [
        ("SourceType", "Source type"),
        ("ParticleType", "Particle type"),
        ("EnergyMeV", "Energy [MeV]"),
        ("BeamRadius", "Beam radius [mm]"),
        ("DirectionX", "Direction X"),
        ("DirectionY", "Direction Y"),
        ("DirectionZ", "Direction Z"),
        ("Events", "Events"),
    ],
    "FlowStudio::BCGeant4Detector": [
        ("DetectorType", "Detector type"),
        ("CollectionName", "Collection name"),
        ("ThresholdKeV", "Threshold [keV]"),
        ("PixelsX", "Pixels X"),
        ("PixelsY", "Pixels Y"),
    ],
    "FlowStudio::BCGeant4Scoring": [
        ("ScoreQuantity", "Score quantity"),
        ("ScoringType", "Scoring type"),
        ("BinsX", "Bins X"),
        ("BinsY", "Bins Y"),
        ("BinsZ", "Bins Z"),
        ("NormalizePerEvent", "Normalize per event"),
    ],
}


class TaskGenericBC(FloEFDTaskPanel):
    """Boundary-condition panel generated from known object properties."""

    SUMMARY_DETAIL = (
        "Assign geometry and edit the boundary parameters for {label}."
    )

    def __init__(self, obj):
        self._presenter = GenericBoundaryPresenter()
        super().__init__(obj)

    def _build_task_validation(self):
        level, title, detail = self._presenter.build_validation(self._current_settings())
        if level:
            return level, title, detail
        return super()._build_task_validation()

    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)
        layout.addWidget(QtGui.QLabel(f"<b>{self._title()}</b>"))
        self._add_selection_section(layout)

        params = self._section(layout, "Parameters")
        self._widgets = {}
        for prop, label in BC_FIELDS.get(getattr(self.obj, "FlowType", ""), []):
            if prop not in getattr(self.obj, "PropertiesList", []):
                continue
            value = getattr(self.obj, prop)
            if isinstance(value, bool):
                widget = self._checkbox(value)
            elif isinstance(value, str):
                try:
                    choices = list(self.obj.getEnumerationsOfProperty(prop))
                except Exception:
                    choices = [value]
                widget = self._combo(choices or [value], value)
            else:
                widget = self._spin_float(float(value), -1e15, 1e15, 8, 1.0)
            self._add_row(params, label + ":", widget)
            self._widgets[prop] = widget

        if not self._widgets:
            params.addWidget(QtGui.QLabel("No editable parameters for this boundary condition."))

        layout.addStretch()
        return widget

    def _title(self):
        return getattr(self.obj, "BCLabel", getattr(self.obj, "Label", "Boundary Condition"))

    def _field_names(self):
        field_names = []
        for prop, _label in BC_FIELDS.get(getattr(self.obj, "FlowType", ""), []):
            if prop in getattr(self.obj, "PropertiesList", []):
                field_names.append(prop)
        return field_names

    def _current_settings(self):
        if not hasattr(self, "_widgets"):
            return self._presenter.read_settings(self.obj, self._field_names())

        values = {}
        for prop, widget in self._widgets.items():
            if isinstance(widget, QtGui.QCheckBox):
                values[prop] = widget.isChecked()
            elif isinstance(widget, QtGui.QComboBox):
                values[prop] = widget.currentText()
            else:
                values[prop] = widget.value()

        return GenericBoundarySettings(
            title=self._title(),
            flow_type=getattr(self.obj, "FlowType", ""),
            references=tuple(self._refs()),
            values=values,
        )

    def _store(self):
        self._presenter.persist_settings(self.obj, self._current_settings())
