#pragma once

// SPDX-License-Identifier: LGPL-2.1-or-later

#ifdef _MSC_VER
  #ifdef SheetMetal_EXPORTS
    #define SheetMetalExport __declspec(dllexport)
  #else
    #define SheetMetalExport __declspec(dllimport)
  #endif
#else
  #define SheetMetalExport
#endif

namespace Mod {
namespace SheetMetal {

class SheetMetalExport SheetMetalBend {
public:
    static const char* typeName();
};

} // namespace SheetMetal
} // namespace Mod
