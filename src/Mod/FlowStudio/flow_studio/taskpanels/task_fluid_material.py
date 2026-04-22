# ***************************************************************************
# *   Copyright (c) 2026 FlowStudio contributors                          *
# *   SPDX-License-Identifier: LGPL-2.1-or-later                          *
# ***************************************************************************

"""Task panel for FluidMaterial – FloEFD-like fluid property editor."""

# Predefined material database – kept before PySide import so it can be
# used by tests that run outside FreeCAD.
MATERIALS_DB = {
    "Air (20°C, 1atm)": {
        "Density": 1.225, "DynamicViscosity": 1.81e-5,
        "KinematicViscosity": 1.48e-5, "SpecificHeat": 1005.0,
        "ThermalConductivity": 0.0257, "PrandtlNumber": 0.707,
    },
    "Water (20°C)": {
        "Density": 998.2, "DynamicViscosity": 1.002e-3,
        "KinematicViscosity": 1.004e-6, "SpecificHeat": 4182.0,
        "ThermalConductivity": 0.6, "PrandtlNumber": 7.01,
    },
    "Oil (SAE 30)": {
        "Density": 891.0, "DynamicViscosity": 0.29,
        "KinematicViscosity": 3.25e-4, "SpecificHeat": 1900.0,
        "ThermalConductivity": 0.145, "PrandtlNumber": 3800.0,
    },
    "Glycerin": {
        "Density": 1261.0, "DynamicViscosity": 1.412,
        "KinematicViscosity": 1.12e-3, "SpecificHeat": 2427.0,
        "ThermalConductivity": 0.286, "PrandtlNumber": 11970.0,
    },
    "Mercury": {
        "Density": 13534.0, "DynamicViscosity": 1.526e-3,
        "KinematicViscosity": 1.128e-7, "SpecificHeat": 139.3,
        "ThermalConductivity": 8.514, "PrandtlNumber": 0.025,
    },
}

try:
    from flow_studio.catalog.database import material_presets as _material_presets
    MATERIALS_DB.update(
        {
            name: props
            for name, props in _material_presets("Gases", "Liquids").items()
            if all(
                key in props
                for key in (
                    "Density",
                    "DynamicViscosity",
                    "KinematicViscosity",
                    "SpecificHeat",
                    "ThermalConductivity",
                    "PrandtlNumber",
                )
            )
        }
    )
except Exception:
    pass

try:
    from PySide import QtGui  # noqa: E402
    from flow_studio.taskpanels.task_flowefd_features import FloEFDTaskPanel  # noqa: E402
    _HAS_GUI = True
except ImportError:
    _HAS_GUI = False


class TaskFluidMaterial(FloEFDTaskPanel if _HAS_GUI else object):

    SUMMARY_TITLE = "Fluid Material"
    SUMMARY_DETAIL = (
        "Assign a fluid preset or custom transport properties for {label}."
    )

    def _build_task_validation(self):
        if not self._refs():
            return (
                "incomplete",
                "Assign fluid regions",
                "Select one or more fluid regions so this material assignment applies to geometry.",
            )

        if float(getattr(self.obj, "Density", 0.0)) <= 0.0:
            return (
                "incomplete",
                "Fluid density required",
                "Enter a positive density before solving with this fluid material.",
            )

        if float(getattr(self.obj, "DynamicViscosity", 0.0)) <= 0.0:
            return (
                "incomplete",
                "Dynamic viscosity required",
                "Enter a positive dynamic viscosity for this fluid material.",
            )

        if float(getattr(self.obj, "SpecificHeat", 0.0)) <= 0.0:
            return (
                "warning",
                "Specific heat should be positive",
                "Use a positive specific heat so thermal solves have a valid fluid heat capacity.",
            )

        return super()._build_task_validation()

    def _build_form(self):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout(widget)

        layout.addWidget(QtGui.QLabel("<b>Fluid Material Properties</b>"))
        self._add_selection_section(layout, "Assigned Fluid Region")

        material = self._section(layout, "Material")

        presets = [
            "Custom", "Air (20°C, 1atm)", "Water (20°C)",
            "Oil (SAE 30)", "Glycerin", "Mercury", "R134a",
            "Nitrogen", "Oxygen",
        ]
        presets = sorted(set(presets + list(MATERIALS_DB)))
        if "Custom" in presets:
            presets.remove("Custom")
        presets.insert(0, "Custom")
        self.cb_preset = self._combo(presets, self.obj.Preset)
        self._add_row(material, "Preset:", self.cb_preset)
        self.cb_preset.currentTextChanged.connect(self._on_preset_changed)

        btn_db = QtGui.QPushButton("Engineering Database...")
        btn_db.clicked.connect(self._open_database)
        material.addWidget(btn_db)

        properties = self._section(layout, "Properties")
        self.sp_rho = self._spin_float(self.obj.Density, 0.001, 20000, 4, 0.1)
        self._add_row(properties, "Density [kg/m³]:", self.sp_rho)

        self.sp_mu = self._spin_float(self.obj.DynamicViscosity, 1e-9, 100, 8, 1e-6)
        self._add_row(properties, "Dynamic Viscosity [Pa·s]:", self.sp_mu)

        self.sp_nu = self._spin_float(self.obj.KinematicViscosity, 1e-9, 1, 8, 1e-7)
        self._add_row(properties, "Kinematic Viscosity [m²/s]:", self.sp_nu)

        self.sp_cp = self._spin_float(self.obj.SpecificHeat, 1, 50000, 1, 10)
        self._add_row(properties, "Specific Heat [J/(kg·K)]:", self.sp_cp)

        self.sp_k = self._spin_float(self.obj.ThermalConductivity, 0, 500, 4, 0.01)
        self._add_row(properties, "Thermal Conductivity [W/(m·K)]:", self.sp_k)

        self.sp_pr = self._spin_float(self.obj.PrandtlNumber, 0.001, 100000, 3, 0.01)
        self._add_row(properties, "Prandtl Number:", self.sp_pr)

        layout.addStretch()
        return widget

    def _on_preset_changed(self, text):
        if text in MATERIALS_DB:
            m = MATERIALS_DB[text]
            self.sp_rho.setValue(m["Density"])
            self.sp_mu.setValue(m["DynamicViscosity"])
            self.sp_nu.setValue(m["KinematicViscosity"])
            self.sp_cp.setValue(m["SpecificHeat"])
            self.sp_k.setValue(m["ThermalConductivity"])
            self.sp_pr.setValue(m["PrandtlNumber"])

    def _open_database(self):
        from flow_studio.catalog.editor import show_engineering_database_editor
        show_engineering_database_editor()

    def _store(self):
        self.obj.Preset = self.cb_preset.currentText()
        self.obj.Density = self.sp_rho.value()
        self.obj.DynamicViscosity = self.sp_mu.value()
        self.obj.KinematicViscosity = self.sp_nu.value()
        self.obj.SpecificHeat = self.sp_cp.value()
        self.obj.ThermalConductivity = self.sp_k.value()
        self.obj.PrandtlNumber = self.sp_pr.value()
