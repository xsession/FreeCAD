// SPDX-License-Identifier: LGPL-2.1-or-later

/***************************************************************************
 *   Copyright (c) 2023 Werner Mayer <wmayer[at]users.sourceforge.net>     *
 *                                                                         *
 *   This file is part of FreeCAD.                                         *
 *                                                                         *
 *   FreeCAD is free software: you can redistribute it and/or modify it    *
 *   under the terms of the GNU Lesser General Public License as           *
 *   published by the Free Software Foundation, either version 2.1 of the  *
 *   License, or (at your option) any later version.                       *
 *                                                                         *
 *   FreeCAD is distributed in the hope that it will be useful, but        *
 *   WITHOUT ANY WARRANTY; without even the implied warranty of            *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU      *
 *   Lesser General Public License for more details.                       *
 *                                                                         *
 *   You should have received a copy of the GNU Lesser General Public      *
 *   License along with FreeCAD. If not, see                               *
 *   <https://www.gnu.org/licenses/>.                                      *
 *                                                                         *
 **************************************************************************/


#include <Standard_Version.hxx>
#include <STEPCAFControl_Reader.hxx>
#include <Transfer_TransientProcess.hxx>
#include <XSControl_TransferReader.hxx>
#include <XSControl_WorkSession.hxx>
#include <Interface_Static.hxx>
#include <OSD_Parallel.hxx>

#if OCC_VERSION_HEX >= 0x070600
#include <OSD_ThreadPool.hxx>
#endif

#include <chrono>
#include <thread>


#include "ReaderStep.h"
#include <Base/Console.h>
#include <Base/Exception.h>
#include <Base/FileInfo.h>
#include <Base/Sequencer.h>
#include <Mod/Part/App/encodeFilename.h>

using namespace Import;

ReaderStep::ReaderStep(const Base::FileInfo& file)  // NOLINT
    : file {file}
{
#if OCC_VERSION_HEX >= 0x070800
    codePage = Resource_FormatType_UTF8;
#endif
}

void ReaderStep::read(Handle(TDocStd_Document) hDoc)  // NOLINT
{
    std::string utf8Name = file.filePath();
    std::string name8bit = Part::encodeFilename(utf8Name);

    // --- File size detection for adaptive optimization ---
    int64_t fileSize = file.size();
    bool isMediumFile = fileSize > 10LL * 1024 * 1024;    // > 10 MB
    bool isLargeFile = fileSize > 100LL * 1024 * 1024;    // > 100 MB
    bool isVeryLargeFile = fileSize > 500LL * 1024 * 1024; // > 500 MB

    if (isMediumFile) {
        Base::Console().Message(
            "[STEP Import] File size: %.1f MB — enabling optimizations\n",
            fileSize / (1024.0 * 1024.0));
    }

    // --- Initialize OCC thread pool for parallel processing ---
    unsigned int numThreads = std::thread::hardware_concurrency();
    if (numThreads == 0) {
        numThreads = 4;
    }

#if OCC_VERSION_HEX >= 0x070600
    Handle(OSD_ThreadPool) pool = OSD_ThreadPool::DefaultPool(numThreads);
    (void)pool;  // ensure it's initialized
#endif
    OSD_Parallel::SetUseOcctThreads(true);

    // --- Configure STEP read parameters for parallel processing ---
    Interface_Static::SetIVal("read.step.product.mode", 1);      // assembly structure
    Interface_Static::SetIVal("read.step.product.context", 1);    // all contexts
    Interface_Static::SetIVal("read.step.shape.repr", 1);         // all representations
    Interface_Static::SetIVal("read.step.assembly.level", 1);     // all levels

    // Precision settings — adaptive based on file size
    // Shape healing (edge precision fixing) is the #1 CPU bottleneck for STEP import.
    // Capping max precision prevents OCC from spending minutes healing edge tolerances.
    if (isVeryLargeFile) {
        // Very large files: aggressive relaxation
        Interface_Static::SetIVal("read.precision.mode", 0);      // file precision
        Interface_Static::SetRVal("read.precision.val", 0.001);
        Interface_Static::SetIVal("read.maxprecision.mode", 1);   // capped
        Interface_Static::SetRVal("read.maxprecision.val", 0.1);  // very relaxed healing
        Interface_Static::SetIVal("read.surfacecurve.mode", 0);   // skip recompute
    }
    else if (isLargeFile) {
        Interface_Static::SetIVal("read.precision.mode", 0);      // file precision
        Interface_Static::SetRVal("read.precision.val", 0.0001);
        Interface_Static::SetIVal("read.maxprecision.mode", 1);   // capped
        Interface_Static::SetRVal("read.maxprecision.val", 0.5);  // moderate healing
        Interface_Static::SetIVal("read.surfacecurve.mode", 3);   // prefer 3D
    }
    else if (isMediumFile) {
        // 10-100 MB: cap precision to avoid slow healing on complex models
        Interface_Static::SetIVal("read.precision.mode", 0);      // file precision
        Interface_Static::SetRVal("read.precision.val", 0.0001);
        Interface_Static::SetIVal("read.maxprecision.mode", 1);   // capped
        Interface_Static::SetRVal("read.maxprecision.val", 1.0);  // reasonable cap
        Interface_Static::SetIVal("read.surfacecurve.mode", 3);   // prefer 3D (faster)
    }
    else {
        Interface_Static::SetIVal("read.precision.mode", 1);      // user precision
        Interface_Static::SetRVal("read.precision.val", 0.0001);
        Interface_Static::SetIVal("read.maxprecision.mode", 0);   // file max precision
        Interface_Static::SetRVal("read.maxprecision.val", 1.0);
    }

    // --- Parse phase (timed) ---
    auto parseStart = std::chrono::steady_clock::now();

    STEPCAFControl_Reader aReader;
    aReader.SetColorMode(true);
    aReader.SetNameMode(true);
    aReader.SetLayerMode(true);
    aReader.SetSHUOMode(true);
#if OCC_VERSION_HEX < 0x070800
    if (aReader.ReadFile(name8bit.c_str()) != IFSelect_RetDone) {
#else
    Handle(StepData_StepModel) aStepModel = new StepData_StepModel;
    aStepModel->InternalParameters.InitFromStatic();
    aStepModel->SetSourceCodePage(codePage);
    if (aReader.ReadFile(name8bit.c_str(), aStepModel->InternalParameters) != IFSelect_RetDone) {
#endif
        throw Base::FileException("Cannot read STEP file", file);
    }

    auto parseEnd = std::chrono::steady_clock::now();
    parseTimeMs = std::chrono::duration_cast<std::chrono::milliseconds>(parseEnd - parseStart).count();

    // Report entity count for large files
    auto nRoots = aReader.NbRootsForTransfer();
    Base::Console().Message(
        "[STEP Import] Parse complete in %.1fs — %d root entities\n",
        parseTimeMs / 1000.0, (int)nRoots);

    // --- Transfer phase (timed) ---
    // Use a SequencerLauncher so the GUI progress bar pumps events
    // and the application stays responsive during the long transfer.
    auto transferStart = std::chrono::steady_clock::now();

    {
        Base::SequencerLauncher seq("Transferring STEP geometry...", nRoots);
        aReader.Transfer(hDoc);
    }

    auto transferEnd = std::chrono::steady_clock::now();
    transferTimeMs = std::chrono::duration_cast<std::chrono::milliseconds>(transferEnd - transferStart).count();

    totalTimeMs = parseTimeMs + transferTimeMs;
    fileSizeBytes = fileSize;

    Base::Console().Message(
        "[STEP Import] Transfer complete in %.1fs — total %.1fs\n",
        transferTimeMs / 1000.0, totalTimeMs / 1000.0);
}
