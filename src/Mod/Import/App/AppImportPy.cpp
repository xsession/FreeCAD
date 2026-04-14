// SPDX-License-Identifier: LGPL-2.1-or-later

/***************************************************************************
 *   Copyright (c) 2013 Werner Mayer <wmayer[at]users.sourceforge.net>     *
 *                                                                         *
 *   This file is part of the FreeCAD CAx development system.              *
 *                                                                         *
 *   This library is free software; you can redistribute it and/or         *
 *   modify it under the terms of the GNU Library General Public           *
 *   License as published by the Free Software Foundation; either          *
 *   version 2 of the License, or (at your option) any later version.      *
 *                                                                         *
 *   This library  is distributed in the hope that it will be useful,      *
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
 *   GNU Library General Public License for more details.                  *
 *                                                                         *
 *   You should have received a copy of the GNU Library General Public     *
 *   License along with this library; see the file COPYING.LIB. If not,    *
 *   write to the Free Software Foundation, Inc., 59 Temple Place,         *
 *   Suite 330, Boston, MA  02111-1307, USA                                *
 *                                                                         *
 ***************************************************************************/

#if defined(__MINGW32__)
# define WNT  // avoid conflict with GUID
#endif

#include <boost/algorithm/string/predicate.hpp>
#include <boost/range/adaptor/indexed.hpp>
#if defined(__clang__)
# pragma clang diagnostic push
# pragma clang diagnostic ignored "-Wextra-semi"
#endif
#include <Interface_Static.hxx>
#include <OSD_Exception.hxx>
#include <Standard_Version.hxx>
#include <TColStd_IndexedDataMapOfStringString.hxx>
#include <TDocStd_Document.hxx>
#include <Transfer_TransientProcess.hxx>
#include <XCAFApp_Application.hxx>
#include <XCAFDoc_DocumentTool.hxx>
#include <XSControl_TransferReader.hxx>
#include <XSControl_WorkSession.hxx>
#include <Message_ProgressRange.hxx>

#if defined(__clang__)
# pragma clang diagnostic pop
#endif

#include <chrono>
#include <vector>
#include <cmath>
#include <thread>
#include <future>
#include <algorithm>
#include <mutex>

#include <BRep_Builder.hxx>
#include <BRepMesh_IncrementalMesh.hxx>
#include <IMeshTools_Parameters.hxx>
#include <Precision.hxx>
#include <TopExp.hxx>
#include <TopTools_IndexedMapOfShape.hxx>
#include <TopoDS_Compound.hxx>
#include <TopoDS_Shape.hxx>
#include <gp.hxx>

#include <Mod/Part/App/PartFeature.h>
#include <Mod/Part/App/Tools.h>

#include "dxf/ImpExpDxf.h"
#include "SketchExportHelper.h"
#include <App/Application.h>
#include <App/Document.h>
#include <App/DocumentObjectPy.h>
#include <Base/Console.h>
#include <Base/PyWrapParseTupleAndKeywords.h>
#include <Mod/Part/App/ImportIges.h>
#include <Mod/Part/App/ImportStep.h>
#include <Mod/Part/App/Interface.h>
#include <Mod/Part/App/OCAF/ImportExportSettings.h>
#include <Mod/Part/App/PartFeaturePy.h>
#include <Mod/Part/App/TopoShapePy.h>
#include <Mod/Part/App/encodeFilename.h>

#include "ImportOCAF2.h"
#include "ReaderGltf.h"
#include "ReaderIges.h"
#include "ReaderStep.h"
#include "WriterGltf.h"
#include "WriterIges.h"
#include "WriterStep.h"

namespace Import
{

namespace
{

struct StepImportPerfProfile
{
    bool speedMode = false;
    bool reduceObjects = false;
    double minMeshDeviation = 0.0;
    double minAngularDeflection = 0.0;
};

StepImportPerfProfile getStepImportPerfProfile(const Base::FileInfo& file)
{
    StepImportPerfProfile profile;
    if (!file.hasExtension({"stp", "step"})) {
        return profile;
    }

    const int64_t fileSize = file.size();
    const bool isMedium = fileSize > 25LL * 1024 * 1024;
    const bool isLarge = fileSize > 100LL * 1024 * 1024;
    const bool isVeryLarge = fileSize > 500LL * 1024 * 1024;

    profile.speedMode = isMedium;
    profile.reduceObjects = isLarge;

    if (isVeryLarge) {
        profile.minMeshDeviation = 5.0;
        profile.minAngularDeflection = 40.0;
    }
    else if (isLarge) {
        profile.minMeshDeviation = 2.5;
        profile.minAngularDeflection = 33.0;
    }
    else if (isMedium) {
        profile.minMeshDeviation = 1.0;
        profile.minAngularDeflection = 30.0;
    }

    return profile;
}

}  // namespace

class Module: public Py::ExtensionModule<Module>
{
public:
    Module()
        : Py::ExtensionModule<Module>("Import")
    {
        add_keyword_method(
            "open",
            &Module::importer,
            "open(string) -- Open the file and create a new document."
        );
        add_keyword_method(
            "insert",
            &Module::importer,
            "insert(string,string) -- Insert the file into the given document."
        );
        add_keyword_method(
            "export",
            &Module::exporter,
            "export(list,string) -- Export a list of objects into a single file."
        );
        add_varargs_method(
            "readDXF",
            &Module::readDXF,
            "readDXF(filename,[document,ignore_errors,option_source]): Imports a "
            "DXF file into the given document. ignore_errors is True by default."
        );
        add_varargs_method(
            "writeDXFShape",
            &Module::writeDXFShape,
            "writeDXFShape([shape],filename [version,usePolyline,optionSource]): "
            "Exports Shape(s) to a DXF file."
        );
        add_varargs_method(
            "writeDXFObject",
            &Module::writeDXFObject,
            "writeDXFObject([objects],filename [,version,usePolyline,optionSource]): Exports "
            "DocumentObject(s) to a DXF file."
        );
        initialize("This module is the Import module.");  // register with Python
    }

    ~Module() override = default;

private:
    Py::Object importer(const Py::Tuple& args, const Py::Dict& kwds)
    {
        char* Name = nullptr;
        char* DocName = nullptr;
        PyObject* importHidden = Py_None;
        PyObject* merge = Py_None;
        PyObject* useLinkGroup = Py_None;
        int mode = -1;
        static const std::array<const char*, 7>
            kwd_list {"name", "docName", "importHidden", "merge", "useLinkGroup", "mode", nullptr};
        if (!Base::Wrapped_ParseTupleAndKeywords(
                args.ptr(),
                kwds.ptr(),
                "et|sO!O!O!i",
                kwd_list,
                "utf-8",
                &Name,
                &DocName,
                &PyBool_Type,
                &importHidden,
                &PyBool_Type,
                &merge,
                &PyBool_Type,
                &useLinkGroup,
                &mode
            )) {
            throw Py::Exception();
        }

        std::string Utf8Name = std::string(Name);
        PyMem_Free(Name);

        try {
            Base::FileInfo file(Utf8Name.c_str());

            App::Document* pcDoc = nullptr;
            if (DocName) {
                pcDoc = App::GetApplication().getDocument(DocName);
            }
            if (!pcDoc) {
                pcDoc = App::GetApplication().newDocument();
            }

            Handle(XCAFApp_Application) hApp = XCAFApp_Application::GetApplication();
            Handle(TDocStd_Document) hDoc;
            hApp->NewDocument(TCollection_ExtendedString("MDTV-CAF"), hDoc);

            if (file.hasExtension({"stp", "step"})) {
                try {
                    Import::ReaderStep reader(file);
                    reader.read(hDoc);

                    // Log timing information for STEP imports
                    Base::Console().Message(
                        "[STEP Import] File: %s (%.1f MB)\n"
                        "[STEP Import] Parse: %.1fs, Transfer: %.1fs, Total: %.1fs\n",
                        Utf8Name.c_str(),
                        reader.getFileSizeBytes() / (1024.0 * 1024.0),
                        reader.getParseTimeMs() / 1000.0,
                        reader.getTransferTimeMs() / 1000.0,
                        reader.getTotalTimeMs() / 1000.0);
                }
                catch (OSD_Exception& e) {
                    Base::Console().error("%s\n", e.GetMessageString());
                    Base::Console().message("Try to load STEP file without colors...\n");

                    Part::ImportStepParts(pcDoc, Utf8Name.c_str());
                    pcDoc->recompute();
                }
            }
            else if (file.hasExtension({"igs", "iges"})) {
                try {
                    Import::ReaderIges reader(file);
                    reader.read(hDoc);
                }
                catch (OSD_Exception& e) {
                    Base::Console().error("%s\n", e.GetMessageString());
                    Base::Console().message("Try to load IGES file without colors...\n");

                    Part::ImportIgesParts(pcDoc, Utf8Name.c_str());
                    pcDoc->recompute();
                }
            }
            else if (file.hasExtension({"glb", "gltf"})) {
                Import::ReaderGltf reader(file);
                reader.read(hDoc);
            }
            else {
                throw Py::Exception(PyExc_IOError, "no supported file format");
            }

            ImportOCAFExt ocaf(hDoc, pcDoc, file.fileNamePure());
            auto ocafOptions = ImportOCAFExt::customImportOptions();
            const auto perfProfile = getStepImportPerfProfile(file);
            if (perfProfile.speedMode) {
                // Large STEP assemblies render and navigate much faster when we avoid
                // collapsing everything into one heavy compound.
                ocafOptions.merge = false;
                ocafOptions.useLinkGroup = true;
                ocafOptions.reduceObjects = perfProfile.reduceObjects;
            }
            ocaf.setImportOptions(ocafOptions);
            if (merge != Py_None) {
                ocaf.setMerge(Base::asBoolean(merge));
            }
            if (importHidden != Py_None) {
                ocaf.setImportHiddenObject(Base::asBoolean(importHidden));
            }
            if (useLinkGroup != Py_None) {
                ocaf.setUseLinkGroup(Base::asBoolean(useLinkGroup));
            }
            if (mode >= 0) {
                ocaf.setMode(mode);
            }

            // Record existing objects to identify newly created ones
            std::set<App::DocumentObject*> existingObjs(
                pcDoc->getObjects().begin(), pcDoc->getObjects().end());

            ocaf.loadShapes();

            // Batch-tessellate all newly imported shapes in parallel.
            // ImportOCAF2::loadShapes() already clears ObjImporting flags,
            // so this runs after import is complete. Pre-tessellating here
            // avoids serial tessellation in the GUI thread on first render.
            {
                auto allObjs = pcDoc->getObjects();
                std::vector<App::DocumentObject*> newObjs;
                for (auto* obj : allObjs) {
                    if (existingObjs.find(obj) == existingObjs.end()) {
                        newObjs.push_back(obj);
                    }
                }

                // Collect all imported shapes for parallel tessellation.
                // OCCT's InParallel relies on TBB which may not be linked,
                // so we use explicit std::thread workers for reliable parallelism.
                std::vector<TopoDS_Shape> shapes;
                shapes.reserve(newObjs.size());

                for (auto* obj : newObjs) {
                    auto* partFeature = dynamic_cast<Part::Feature*>(obj);
                    if (!partFeature) {
                        continue;
                    }
                    const TopoDS_Shape& shape = partFeature->Shape.getValue();
                    if (shape.IsNull()) {
                        continue;
                    }
                    shapes.push_back(shape);
                }

                if (!shapes.empty()) {
                    ParameterGrp::handle hPart = App::GetApplication().GetParameterGroupByPath(
                        "User parameter:BaseApp/Preferences/Mod/Part"
                    );
                    double deviation = hPart->GetFloat("MeshDeviation", 0.2);
                    double angularDeflection = hPart->GetFloat("MeshAngularDeflection", 28.65);
                    bool useAdaptive = hPart->GetBool("AdaptiveDeviation", true);
                    int faceThreshold = hPart->GetInt("AdaptiveDeviationFaceThreshold", 2000);
                    double maxScale = hPart->GetFloat("AdaptiveDeviationMaxScale", 10.0);

                    if (perfProfile.speedMode) {
                        deviation = std::max(deviation, perfProfile.minMeshDeviation);
                        angularDeflection = std::max(
                            angularDeflection, perfProfile.minAngularDeflection);
                        Base::Console().Message(
                            "Import: Speed mode enabled for %.1f MB STEP file "
                            "(deviation %.2f, angular %.1f deg)\n",
                            file.size() / (1024.0 * 1024.0),
                            deviation,
                            angularDeflection);
                    }

                    // Count total faces for adaptive deviation
                    BRep_Builder builder;
                    TopoDS_Compound compound;
                    builder.MakeCompound(compound);
                    for (auto& s : shapes) {
                        builder.Add(compound, s);
                    }

                    double dev = deviation;
                    if (useAdaptive && faceThreshold > 0) {
                        TopTools_IndexedMapOfShape faceMap;
                        TopExp::MapShapes(compound, TopAbs_FACE, faceMap);
                        int totalFaces = faceMap.Extent();
                        if (totalFaces > faceThreshold) {
                            double scale = std::sqrt(static_cast<double>(totalFaces) / faceThreshold);
                            scale = std::min(scale, maxScale);
                            dev *= scale;
                            if (totalFaces > faceThreshold * 5) {
                                angularDeflection = std::max(angularDeflection, 33.0);
                            }
                            Base::Console().Message(
                                "Import: Adaptive tessellation for %d faces (deviation x%.2f)\n",
                                totalFaces, scale);
                        }
                    }

                    Standard_Real deflection = Part::Tools::getDeflection(compound, dev);
                    if (deflection < gp::Resolution()) {
                        deflection = Precision::Confusion();
                    }
                    Standard_Real angRads = angularDeflection * M_PI / 180.0;

                    // Parallel tessellation using thread workers.
                    // Each shape is independent — BRepMesh operates on disjoint
                    // topology so concurrent tessellation is safe.
                    unsigned int nThreads = std::thread::hardware_concurrency();
                    if (nThreads == 0) {
                        nThreads = 4;
                    }
                    nThreads = std::min(nThreads, static_cast<unsigned int>(shapes.size()));

                    Base::Console().Message(
                        "Import: Parallel tessellating %zu shapes across %u threads...\n",
                        shapes.size(), nThreads);
                    auto tStart = std::chrono::steady_clock::now();

                    // Worker function: tessellate a range of shapes
                    auto tessellateRange = [&](size_t begin, size_t end) {
                        for (size_t idx = begin; idx < end; ++idx) {
                            IMeshTools_Parameters meshParams;
                            meshParams.Deflection = deflection;
                            meshParams.Relative = Standard_False;
                            meshParams.Angle = angRads;
                            meshParams.InParallel = Standard_False;
                            meshParams.AllowQualityDecrease = Standard_True;
                            BRepMesh_IncrementalMesh(shapes[idx], meshParams);
                        }
                    };

                    if (nThreads <= 1 || shapes.size() <= 1) {
                        // Single-threaded fallback
                        tessellateRange(0, shapes.size());
                    }
                    else {
                        // Distribute shapes across threads
                        std::vector<std::thread> threads;
                        threads.reserve(nThreads);
                        size_t chunkSize = (shapes.size() + nThreads - 1) / nThreads;
                        for (unsigned int t = 0; t < nThreads; ++t) {
                            size_t begin = t * chunkSize;
                            size_t end = std::min(begin + chunkSize, shapes.size());
                            if (begin >= end) break;
                            threads.emplace_back(tessellateRange, begin, end);
                        }
                        for (auto& th : threads) {
                            th.join();
                        }
                    }

                    auto tEnd = std::chrono::steady_clock::now();
                    double elapsed = std::chrono::duration<double>(tEnd - tStart).count();
                    Base::Console().Message(
                        "Import: Parallel tessellation complete: %.2fs for %zu shapes (%u threads)\n",
                        elapsed, shapes.size(), nThreads);
                }
            }

            hApp->Close(hDoc);

            if (!ocaf.partColors.empty()) {
                Py::List list;
                for (auto& it : ocaf.partColors) {
                    Py::Tuple tuple(2);
                    tuple.setItem(0, Py::asObject(it.first->getPyObject()));

                    App::PropertyColorList colors;
                    colors.setValues(it.second);
                    tuple.setItem(1, Py::asObject(colors.getPyObject()));

                    list.append(tuple);
                }

                return list;  // NOLINT
            }
        }
        catch (Standard_Failure& e) {
            throw Py::Exception(Base::PyExc_FC_GeneralError, e.GetMessageString());
        }
        catch (const Base::Exception& e) {
            e.setPyException();
            throw Py::Exception();
        }

        return Py::None();
    }
    Py::Object exporter(const Py::Tuple& args, const Py::Dict& kwds)
    {
        PyObject* object = nullptr;
        char* Name = nullptr;
        PyObject* pyexportHidden = Py_None;
        PyObject* pylegacy = Py_None;
        PyObject* pykeepPlacement = Py_None;
        static const std::array<const char*, 6>
            kwd_list {"obj", "name", "exportHidden", "legacy", "keepPlacement", nullptr};
        if (!Base::Wrapped_ParseTupleAndKeywords(
                args.ptr(),
                kwds.ptr(),
                "Oet|O!O!O!",
                kwd_list,
                &object,
                "utf-8",
                &Name,
                &PyBool_Type,
                &pyexportHidden,
                &PyBool_Type,
                &pylegacy,
                &PyBool_Type,
                &pykeepPlacement
            )) {
            throw Py::Exception();
        }

        std::string Utf8Name = std::string(Name);
        PyMem_Free(Name);

        // clang-format off
        // determine export options
        Part::OCAF::ImportExportSettings settings;

        bool legacyExport = (pylegacy         == Py_None ? settings.getExportLegacy()
                                                         : Base::asBoolean(pylegacy));
        bool exportHidden = (pyexportHidden   == Py_None ? settings.getExportHiddenObject()
                                                         : Base::asBoolean(pyexportHidden));
        bool keepPlacement = (pykeepPlacement == Py_None ? settings.getExportKeepPlacement()
                                                         : Base::asBoolean(pykeepPlacement));
        // clang-format on

        try {
            Py::Sequence list(object);
            std::vector<App::DocumentObject*> objs;
            std::map<Part::Feature*, std::vector<Base::Color>> partColor;
            for (Py::Sequence::iterator it = list.begin(); it != list.end(); ++it) {
                PyObject* item = (*it).ptr();
                if (PyObject_TypeCheck(item, &(App::DocumentObjectPy::Type))) {
                    auto pydoc = static_cast<App::DocumentObjectPy*>(item);
                    objs.push_back(pydoc->getDocumentObjectPtr());
                }
                else if (PyTuple_Check(item) && PyTuple_Size(item) == 2) {
                    Py::Tuple tuple(*it);
                    Py::Object item0 = tuple.getItem(0);
                    Py::Object item1 = tuple.getItem(1);
                    if (PyObject_TypeCheck(item0.ptr(), &(App::DocumentObjectPy::Type))) {
                        auto pydoc = static_cast<App::DocumentObjectPy*>(item0.ptr());
                        App::DocumentObject* obj = pydoc->getDocumentObjectPtr();
                        objs.push_back(obj);
                        if (Part::Feature* part = dynamic_cast<Part::Feature*>(obj)) {
                            App::PropertyColorList colors;
                            colors.setPyObject(item1.ptr());
                            partColor[part] = colors.getValues();
                        }
                    }
                }
            }

            Handle(XCAFApp_Application) hApp = XCAFApp_Application::GetApplication();
            Handle(TDocStd_Document) hDoc;
            hApp->NewDocument(TCollection_ExtendedString("MDTV-CAF"), hDoc);

            auto getShapeColors = [partColor](App::DocumentObject* obj, const char* subname) {
                std::map<std::string, Base::Color> cols;
                auto it = partColor.find(dynamic_cast<Part::Feature*>(obj));
                if (it != partColor.end() && boost::starts_with(subname, "Face")) {
                    const auto& colors = it->second;
                    std::string face("Face");
                    for (const auto& element : colors | boost::adaptors::indexed(1)) {
                        cols[face + std::to_string(element.index())] = element.value();
                    }
                }
                return cols;
            };

            Import::ExportOCAF2 ocaf(hDoc, getShapeColors);
            if (!legacyExport || !ocaf.canFallback(objs)) {
                ocaf.setExportOptions(ExportOCAF2::customExportOptions());
                ocaf.setExportHiddenObject(exportHidden);
                ocaf.setKeepPlacement(keepPlacement);

                ocaf.exportObjects(objs);
            }
            else {
                bool keepExplicitPlacement = true;
                ExportOCAFCmd ocaf(hDoc, keepExplicitPlacement);
                ocaf.setPartColorsMap(partColor);
                ocaf.exportObjects(objs);
            }

            Base::FileInfo file(Utf8Name.c_str());
            if (file.hasExtension({"stp", "step"})) {
                Import::WriterStep writer(file);
                writer.write(hDoc);
            }
            else if (file.hasExtension({"igs", "iges"})) {
                Import::WriterIges writer(file);
                writer.write(hDoc);
            }
            else if (file.hasExtension({"glb", "gltf"})) {
                Import::WriterGltf writer(file);
                writer.write(hDoc);
            }

            hApp->Close(hDoc);
        }
        catch (Standard_Failure& e) {
            throw Py::Exception(Base::PyExc_FC_GeneralError, e.GetMessageString());
        }
        catch (const Base::Exception& e) {
            e.setPyException();
            throw Py::Exception();
        }

        return Py::None();
    }

    // This readDXF method is an almost exact duplicate of the one in ImportGui::Module.
    // The only difference is the CDxfRead class derivation that is created.
    // It would seem desirable to have most of this code in just one place, passing it
    // e.g. a pointer to a function that does the 4 lines during the lifetime of the
    // CDxfRead object, but right now Import::Module and ImportGui::Module cannot see
    // each other's functions so this shared code would need some place to live where
    // both places could include a declaration.
    Py::Object readDXF(const Py::Tuple& args)
    {
        char* Name = nullptr;
        const char* DocName = nullptr;
        const char* optionSource = nullptr;
        std::string defaultOptions = "User parameter:BaseApp/Preferences/Mod/Draft";
        bool IgnoreErrors = true;
        if (
            !PyArg_ParseTuple(args.ptr(), "et|sbs", "utf-8", &Name, &DocName, &IgnoreErrors, &optionSource)
        ) {
            throw Py::Exception();
        }

        std::string EncodedName = std::string(Name);
        PyMem_Free(Name);

        Base::FileInfo file(EncodedName.c_str());
        if (!file.exists()) {
            throw Py::RuntimeError("File doesn't exist");
        }

        if (optionSource) {
            defaultOptions = optionSource;
        }

        App::Document* pcDoc = nullptr;
        if (DocName) {
            pcDoc = App::GetApplication().getDocument(DocName);
        }
        else {
            pcDoc = App::GetApplication().getActiveDocument();
        }
        if (!pcDoc) {
            pcDoc = App::GetApplication().newDocument(DocName);
        }

        try {
            // read the DXF file
            ImpExpDxfRead dxf_file(EncodedName, pcDoc);
            dxf_file.setOptionSource(defaultOptions);
            dxf_file.setOptions();

            auto startTime = std::chrono::high_resolution_clock::now();
            dxf_file.DoRead(IgnoreErrors);
            auto endTime = std::chrono::high_resolution_clock::now();
            std::chrono::duration<double> elapsed = endTime - startTime;
            dxf_file.setImportTime(elapsed.count());

            pcDoc->recompute();
            return dxf_file.getStatsAsPyObject();
        }
        catch (const Standard_Failure& e) {
            throw Py::RuntimeError(e.GetMessageString());
        }
        catch (const Base::Exception& e) {
            throw Py::RuntimeError(e.what());
        }
    }


    Py::Object writeDXFShape(const Py::Tuple& args)
    {
        Base::Console().message("Imp:writeDXFShape()\n");
        PyObject* shapeObj = nullptr;
        char* fname = nullptr;
        std::string filePath;
        std::string layerName;
        const char* optionSource = nullptr;
        std::string defaultOptions = "User parameter:BaseApp/Preferences/Mod/Draft";
        int versionParm = -1;
        bool versionOverride = false;
        bool polyOverride = false;
        PyObject* usePolyline = Py_False;

        // handle list of shapes
        if (PyArg_ParseTuple(
                args.ptr(),
                "O!et|iOs",
                &(PyList_Type),
                &shapeObj,
                "utf-8",
                &fname,
                &versionParm,
                &usePolyline,
                &optionSource
            )) {
            filePath = std::string(fname);
            layerName = "none";
            PyMem_Free(fname);

            if ((versionParm == 12) || (versionParm == 14)) {
                versionOverride = true;
            }
            if (usePolyline == Py_True) {
                polyOverride = true;
            }
            if (optionSource) {
                defaultOptions = optionSource;
            }

            try {
                ImpExpDxfWrite writer(filePath);
                writer.setOptionSource(defaultOptions);
                writer.setOptions();
                if (versionOverride) {
                    writer.setVersion(versionParm);
                }
                writer.setPolyOverride(polyOverride);
                writer.setLayerName(layerName);
                writer.init();
                Py::Sequence list(shapeObj);
                for (Py::Sequence::iterator it = list.begin(); it != list.end(); ++it) {
                    if (PyObject_TypeCheck((*it).ptr(), &(Part::TopoShapePy::Type))) {
                        Part::TopoShape* ts
                            = static_cast<Part::TopoShapePy*>((*it).ptr())->getTopoShapePtr();
                        TopoDS_Shape shape = ts->getShape();
                        writer.exportShape(shape);
                    }
                }
                writer.endRun();
                return Py::None();
            }
            catch (const Base::Exception& e) {
                throw Py::RuntimeError(e.what());
            }
        }

        PyErr_Clear();
        if (PyArg_ParseTuple(
                args.ptr(),
                "O!et|iOs",
                &(Part::TopoShapePy::Type),
                &shapeObj,
                "utf-8",
                &fname,
                &versionParm,
                &usePolyline,
                &optionSource
            )) {
            filePath = std::string(fname);
            layerName = "none";
            PyMem_Free(fname);

            if ((versionParm == 12) || (versionParm == 14)) {
                versionOverride = true;
            }
            if (usePolyline == Py_True) {
                polyOverride = true;
            }
            if (optionSource) {
                defaultOptions = optionSource;
            }

            try {
                ImpExpDxfWrite writer(filePath);
                writer.setOptionSource(defaultOptions);
                writer.setOptions();
                if (versionOverride) {
                    writer.setVersion(versionParm);
                }
                writer.setPolyOverride(polyOverride);
                writer.setLayerName(layerName);
                writer.init();
                Part::TopoShape* obj = static_cast<Part::TopoShapePy*>(shapeObj)->getTopoShapePtr();
                TopoDS_Shape shape = obj->getShape();
                writer.exportShape(shape);
                writer.endRun();
                return Py::None();
            }
            catch (const Base::Exception& e) {
                throw Py::RuntimeError(e.what());
            }
        }

        throw Py::TypeError("expected ([Shape],path");
    }

    Py::Object writeDXFObject(const Py::Tuple& args)
    {
        PyObject* docObj = nullptr;
        char* fname = nullptr;
        std::string filePath;
        std::string layerName;
        const char* optionSource = nullptr;
        std::string defaultOptions = "User parameter:BaseApp/Preferences/Mod/Draft";
        int versionParm = -1;
        bool versionOverride = false;
        bool polyOverride = false;
        PyObject* usePolyline = Py_False;

        if (PyArg_ParseTuple(
                args.ptr(),
                "O!et|iOs",
                &(PyList_Type),
                &docObj,
                "utf-8",
                &fname,
                &versionParm,
                &usePolyline,
                &optionSource
            )) {
            filePath = std::string(fname);
            layerName = "none";
            PyMem_Free(fname);

            if ((versionParm == 12) || (versionParm == 14)) {
                versionOverride = true;
            }
            if (usePolyline == Py_True) {
                polyOverride = true;
            }

            if (optionSource) {
                defaultOptions = optionSource;
            }

            try {
                ImpExpDxfWrite writer(filePath);
                writer.setOptionSource(defaultOptions);
                writer.setOptions();
                if (versionOverride) {
                    writer.setVersion(versionParm);
                }
                writer.setPolyOverride(polyOverride);
                writer.setLayerName(layerName);
                writer.init();
                Py::Sequence list(docObj);
                for (Py::Sequence::iterator it = list.begin(); it != list.end(); ++it) {
                    if (PyObject_TypeCheck((*it).ptr(), &(Part::PartFeaturePy::Type))) {
                        PyObject* item = (*it).ptr();
                        App::DocumentObject* obj
                            = static_cast<App::DocumentObjectPy*>(item)->getDocumentObjectPtr();
                        layerName = obj->getNameInDocument();
                        writer.setLayerName(layerName);
                        TopoDS_Shape shapeToExport;
                        if (SketchExportHelper::isSketch(obj)) {
                            // project sketch along sketch Z via hlrProjector to get geometry on XY
                            // plane
                            shapeToExport = SketchExportHelper::getFlatSketchXY(obj);
                        }
                        else {
                            // do we know that obj is a Part::Feature? is this checked somewhere
                            // before this? this should be a located shape??
                            Part::Feature* part = static_cast<Part::Feature*>(obj);
                            shapeToExport = part->Shape.getValue();
                        }
                        writer.exportShape(shapeToExport);
                    }
                }
                writer.endRun();
                return Py::None();
            }
            catch (const Base::Exception& e) {
                throw Py::RuntimeError(e.what());
            }
        }

        PyErr_Clear();
        if (PyArg_ParseTuple(
                args.ptr(),
                "O!et|iOs",
                &(App::DocumentObjectPy::Type),
                &docObj,
                "utf-8",
                &fname,
                &versionParm,
                &usePolyline,
                &optionSource
            )) {
            filePath = std::string(fname);
            layerName = "none";
            PyMem_Free(fname);
            App::DocumentObject* obj
                = static_cast<App::DocumentObjectPy*>(docObj)->getDocumentObjectPtr();
            Base::Console().message("Imp:writeDXFObject - docObj: %s\n", obj->getNameInDocument());

            if ((versionParm == 12) || (versionParm == 14)) {
                versionOverride = true;
            }
            if (usePolyline == Py_True) {
                polyOverride = true;
            }

            if (optionSource) {
                defaultOptions = optionSource;
            }

            try {
                ImpExpDxfWrite writer(filePath);
                writer.setOptionSource(defaultOptions);
                writer.setOptions();
                if (versionOverride) {
                    writer.setVersion(versionParm);
                }
                writer.setPolyOverride(polyOverride);
                writer.setLayerName(layerName);
                writer.init();
                App::DocumentObject* obj
                    = static_cast<App::DocumentObjectPy*>(docObj)->getDocumentObjectPtr();
                layerName = obj->getNameInDocument();
                writer.setLayerName(layerName);
                TopoDS_Shape shapeToExport;
                if (SketchExportHelper::isSketch(obj)) {
                    // project sketch along sketch Z via hlrProjector to get geometry on XY plane
                    shapeToExport = SketchExportHelper::getFlatSketchXY(obj);
                }
                else {
                    // TODO: do we know that obj is a Part::Feature? is this checked somewhere
                    // before this?
                    // TODO: this should be a located shape??
                    Part::Feature* part = static_cast<Part::Feature*>(obj);
                    shapeToExport = part->Shape.getValue();
                }
                writer.exportShape(shapeToExport);
                writer.endRun();
                return Py::None();
            }
            catch (const Base::Exception& e) {
                throw Py::RuntimeError(e.what());
            }
        }

        throw Py::TypeError("expected ([DocObject],path");
    }
};


PyObject* initModule()
{
    return Base::Interpreter().addModule(new Module);
}

}  // namespace Import
