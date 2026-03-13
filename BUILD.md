# Building FreeCAD

> Comprehensive build, test, and deploy guide for FreeCAD.  
> Covers Windows, Linux, and macOS.

---

## Prerequisites

| Component | Minimum Version | Notes |
|-----------|----------------|-------|
| C++ Compiler | C++17 support | MSVC 2019+, GCC 10+, Clang 12+ |
| CMake | 3.22+ | Required for presets |
| Python | 3.10+ | With development headers |
| Qt | 5.15+ or 6.5+ | Qt6 preferred |
| OpenCASCADE | 7.6+ | 7.8+ recommended for STEP parallelism |
| Coin3D | 4.0+ | 3D rendering |
| pixi | latest | Recommended package manager |

---

## Build Paths

### Path 1: Pixi (Recommended)

Pixi manages all dependencies automatically:

```bash
# Install pixi (if not installed)
curl -fsSL https://pixi.sh/install.sh | bash

# Build FreeCAD
pixi run configure
pixi run build

# Run
pixi run start
```

### Path 2: Conda

```bash
conda env create -f environment.yml
conda activate freecad
cmake --preset conda-release
cmake --build build --parallel
```

### Path 3: System Packages (Linux)

```bash
# Ubuntu/Debian
sudo apt install cmake g++ python3-dev qtbase5-dev libocct-dev libcoin-dev

cmake -B build -S . -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel $(nproc)
```

---

## Running Tests

```bash
# All tests
ctest --test-dir build --output-on-failure

# Specific test suite
ctest --test-dir build -R "FeatureFilletRobustness" --output-on-failure

# Specific test executable
./build/tests/PartDesign_tests_run

# Only stability-fix tests (from this patch)
ctest --test-dir build -R "FeatureFilletRobustness|FeatureChamferRobustness|AssemblyRobustness|DocumentRecompute|ChamferTNP" --output-on-failure

# Run with verbose output
ctest --test-dir build -V
```

---

## Windows One-Command Build

```cmd
build.bat
```

See `build.bat` for all available sub-commands (`configure`, `build`, `test`, `run`, `clean`, etc.).

---

## Packaging with CPack

```bash
# Windows (NSIS installer)
cmake --build build --target package

# Linux (DEB)
cd build && cpack -G DEB

# Linux (RPM)
cd build && cpack -G RPM

# macOS (DMG)
cd build && cpack -G DragNDrop

# Source package
cd build && cpack --config CPackSourceConfig.cmake
```

---

## Troubleshooting

### Build Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `GTest not found` | Missing Google Test submodule | `git submodule update --init` |
| `Qt not found` | Qt not in PATH | Set `CMAKE_PREFIX_PATH` or use pixi |
| `OCC not found` | OpenCASCADE not installed | Install via package manager or pixi |
| `Python.h not found` | Missing Python dev headers | Install `python3-dev` package |

### Test Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Cannot find *.pyd` | DLLs not in PATH (Windows) | Run from build/bin directory |
| Test hangs | GUI test needs display | Set `QT_QPA_PLATFORM=offscreen` |
| `Segfault in test` | Missing test data | Run `cmake --build build --target PartTestData` |

### Packaging Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `NSIS not found` | NSIS not installed | Install from nsis.sourceforge.io |
| `rpmbuild not found` | RPM tools missing | `sudo apt install rpm` |
| `hdiutil failed` | Not on macOS | DMG packaging only works on macOS |

---

*See also: [CHANGELOG_PATCH.md](CHANGELOG_PATCH.md) for the complete patch changelog.*
