// SPDX-License-Identifier: LGPL-2.1-or-later
// Minimal module entry point so MSVC generates a .lib import library for SheetMetal.pyd

#include <Python.h>

static PyModuleDef SheetMetalModule = {
    PyModuleDef_HEAD_INIT,
    "SheetMetal",
    nullptr,
    -1,
    nullptr
};

PyMODINIT_FUNC PyInit_SheetMetal()
{
    return PyModule_Create(&SheetMetalModule);
}
