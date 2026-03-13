// SPDX-License-Identifier: LGPL-2.1-or-later

/***************************************************************************
 *   Copyright (c) 2015 Yorik van Havre (yorik@uncreated.net)              *
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


#include <Standard_Version.hxx>
#if OCC_VERSION_HEX < 0x070600
# include <BRepAdaptor_HCurve.hxx>
#endif
#include <Approx_Curve3d.hxx>
#include <BRepAdaptor_CompCurve.hxx>
#include <BRepAdaptor_Curve.hxx>
#include <BRepBuilderAPI_MakeEdge.hxx>
#include <BRepBuilderAPI_MakeVertex.hxx>
#include <BRepBuilderAPI_MakeWire.hxx>
#include <BRepBuilderAPI_Transform.hxx>
#include <BRepBuilderAPI_GTransform.hxx>
#include <BRep_Tool.hxx>
#include <BRep_Builder.hxx>
#include <GCPnts_UniformAbscissa.hxx>
#include <GeomAPI_Interpolate.hxx>
#include <GeomAPI_PointsToBSpline.hxx>
#include <Geom_Circle.hxx>
#include <Geom_Ellipse.hxx>
#include <Geom_Line.hxx>
#include <Geom_BSplineCurve.hxx>
#include <TColgp_Array1OfPnt.hxx>
#include <TopExp.hxx>
#include <TopExp_Explorer.hxx>
#include <TopoDS.hxx>
#include <TopoDS_Compound.hxx>
#include <TopoDS_Edge.hxx>
#include <TopoDS_Shape.hxx>
#include <TopoDS_Vertex.hxx>
#include <TopoDS_Wire.hxx>
#include <gp_Ax1.hxx>
#include <gp_Ax2.hxx>
#include <gp_Circ.hxx>
#include <gp_Dir.hxx>
#include <gp_Elips.hxx>
#include <gp_Pnt.hxx>
#include <gp_Trsf.hxx>
#include <Precision.hxx>
#include <gp_Vec.hxx>

#include <fstream>
#include <App/Annotation.h>
#include <App/Application.h>
#include <App/Document.h>
#include <App/DocumentObjectGroup.h>
#include <App/DocumentObjectPy.h>
#include <App/FeaturePythonPyImp.h>
#include <Base/Console.h>
#include <Base/Interpreter.h>
#include <Base/Matrix.h>
#include <Base/Parameter.h>
#include <Base/Vector3D.h>
#include <Base/PlacementPy.h>
#include <Mod/Part/App/PartFeature.h>
#include <Mod/Part/App/FeatureCompound.h>
#include <Mod/Part/App/PrimitiveFeature.h>
#include <Mod/Part/App/FeaturePartCircle.h>
#include <App/Link.h>
#include <App/FeaturePython.h>
#include <Base/Tools.h>

#include "ImpExpDxf.h"
#include "ImpExpDxfHelpers.h"


using namespace Import;
using namespace Import::detail;

// Safety net for MSVC 2019 (v19.29) which has a buggy C++20 parenthesized
// aggregate initialization implementation that can ICE in the code generator.
// The real fix is the explicit GeometryBuilder constructor in ImpExpDxf.h.
// MSVC 2022 (v19.30+) does not have this issue.
#if defined(_MSC_VER) && _MSC_VER < 1930
#pragma optimize("", off)
#endif

#if OCC_VERSION_HEX >= 0x070600
using BRepAdaptor_HCurve = BRepAdaptor_Curve;
#endif


TopoDS_Wire ImpExpDxfRead::BuildWireFromPolyline(std::list<VertexInfo>& vertices, int flags)
{
    BRepBuilderAPI_MakeWire wireBuilder;
    bool is_closed = ((flags & 1) != 0);
    if (vertices.empty()) {
        return wireBuilder.Wire();
    }

    auto it = vertices.begin();
    auto prev_it = it++;

    while (it != vertices.end()) {
        const VertexInfo& start_vertex = *prev_it;
        const VertexInfo& end_vertex = *it;
        TopoDS_Edge edge;

        if (start_vertex.bulge == 0.0) {
            edge = BRepBuilderAPI_MakeEdge(
                       makePoint(start_vertex.location),
                       makePoint(end_vertex.location)
            )
                       .Edge();
        }
        else {
            double cot = ((1.0 / start_vertex.bulge) - start_vertex.bulge) / 2.0;
            double center_x = ((start_vertex.location.x + end_vertex.location.x)
                               - (end_vertex.location.y - start_vertex.location.y) * cot)
                / 2.0;
            double center_y = ((start_vertex.location.y + end_vertex.location.y)
                               + (end_vertex.location.x - start_vertex.location.x) * cot)
                / 2.0;
            double center_z = (start_vertex.location.z + end_vertex.location.z) / 2.0;
            Base::Vector3d center(center_x, center_y, center_z);

            gp_Pnt p0 = makePoint(start_vertex.location);
            gp_Pnt p1 = makePoint(end_vertex.location);
            gp_Dir up(0, 0, 1);
            if (start_vertex.bulge < 0) {
                up.Reverse();
            }
            gp_Pnt pc = makePoint(center);
            gp_Circ circle(gp_Ax2(pc, up), p0.Distance(pc));
            if (circle.Radius() > 1e-9) {
                edge = BRepBuilderAPI_MakeEdge(circle, p0, p1).Edge();
            }
        }

        if (!edge.IsNull()) {
            wireBuilder.Add(edge);
        }
        prev_it = it++;
    }

    if (is_closed && vertices.size() > 1) {
        const VertexInfo& start_vertex = vertices.back();
        const VertexInfo& end_vertex = vertices.front();

        // check if the vertices are coincident (distance < tolerance)
        // if they are, the polyline is already closed and we don't need a closing edge
        gp_Pnt p0 = makePoint(start_vertex.location);
        gp_Pnt p1 = makePoint(end_vertex.location);
        double distance = p0.Distance(p1);

        if (distance > Precision::Confusion()) {
            TopoDS_Edge edge;

            if (start_vertex.bulge == 0.0) {
                edge = BRepBuilderAPI_MakeEdge(p0, p1).Edge();
            }
            else {
                double cot = ((1.0 / start_vertex.bulge) - start_vertex.bulge) / 2.0;
                double center_x = ((start_vertex.location.x + end_vertex.location.x)
                                   - (end_vertex.location.y - start_vertex.location.y) * cot)
                    / 2.0;
                double center_y = ((start_vertex.location.y + end_vertex.location.y)
                                   + (end_vertex.location.x - start_vertex.location.x) * cot)
                    / 2.0;
                double center_z = (start_vertex.location.z + end_vertex.location.z) / 2.0;
                Base::Vector3d center(center_x, center_y, center_z);

                gp_Dir up(0, 0, 1);
                if (start_vertex.bulge < 0) {
                    up.Reverse();
                }
                gp_Pnt pc = makePoint(center);
                gp_Circ circle(gp_Ax2(pc, up), p0.Distance(pc));
                if (circle.Radius() > 1e-9) {
                    edge = BRepBuilderAPI_MakeEdge(circle, p0, p1).Edge();
                }
            }
            if (!edge.IsNull()) {
                wireBuilder.Add(edge);
            }
        }
    }

    return wireBuilder.Wire();
}

Part::Feature* ImpExpDxfRead::createFlattenedPolylineFeature(const TopoDS_Wire& wire, const char* name)
{
    auto* p = document->addObject<Part::Feature>(document->getUniqueObjectName(name).c_str());
    if (p) {
        p->Shape.setValue(wire);
        IncrementCreatedObjectCount();
    }
    return p;
}

Part::Compound* ImpExpDxfRead::createParametricPolylineCompound(const TopoDS_Wire& wire, const char* name)
{
    auto* p = document->addObject<Part::Compound>(document->getUniqueObjectName(name).c_str());
    IncrementCreatedObjectCount();

    std::vector<App::DocumentObject*> segments;
    TopExp_Explorer explorer(wire, TopAbs_EDGE);

    for (; explorer.More(); explorer.Next()) {
        TopoDS_Edge edge = TopoDS::Edge(explorer.Current());
        App::DocumentObject* segment = nullptr;
        BRepAdaptor_Curve adaptor(edge);

        if (adaptor.GetType() == GeomAbs_Line) {
            segment = createLinePrimitive(edge, document, "Segment");
        }
        else if (adaptor.GetType() == GeomAbs_Circle) {
            segment = createCirclePrimitive(edge, document, "Arc");
        }

        if (segment) {
            IncrementCreatedObjectCount();
            segment->Visibility.setValue(false);
            // We apply styles later, depending on the context
            segments.push_back(segment);
        }
    }
    p->Links.setValues(segments);
    return p;
}

void ImpExpDxfRead::CreateFlattenedPolyline(const TopoDS_Wire& wire, const char* name)
{
    Part::Feature* p = createFlattenedPolylineFeature(wire, name);

    // Perform the context-specific action of adding it to the collector
    if (p) {
        Collector->AddObject(p, name);
    }
}

void ImpExpDxfRead::CreateParametricPolyline(const TopoDS_Wire& wire, const char* name)
{
    Part::Compound* p = createParametricPolylineCompound(wire, name);

    // Perform the context-specific actions (applying styles and adding to the document)
    if (p) {
        // Style the child segments
        for (App::DocumentObject* segment : p->Links.getValues()) {
            ApplyGuiStyles(static_cast<Part::Feature*>(segment));
        }
        // Add the final compound object to the document
        Collector->AddObject(p, name);
    }
}

std::map<std::string, int> ImpExpDxfRead::PreScan(const std::string& filepath)
{
    std::map<std::string, int> counts;
    std::ifstream ifs(filepath);
    if (!ifs) {
        // Could throw an exception or log an error
        return counts;
    }

    std::string line;
    bool next_is_entity_name = false;

    while (std::getline(ifs, line)) {
        // Simple trim for Windows-style carriage returns
        if (!line.empty() && line.back() == '\r') {
            line.pop_back();
        }

        if (next_is_entity_name) {
            // The line after a "  0" group code is the entity type
            counts[line]++;
            next_is_entity_name = false;
        }
        else if (line == "  0") {
            next_is_entity_name = true;
        }
    }
    return counts;
}

//******************************************************************************
// reading
ImpExpDxfRead::ImpExpDxfRead(const std::string& filepath, App::Document* pcDoc)
    : CDxfRead(filepath)
    , document(pcDoc)
{
    setOptionSource("User parameter:BaseApp/Preferences/Mod/Draft");
    setOptions();
}

void ImpExpDxfRead::StartImport()
{
    CDxfRead::StartImport();
    // Create a hidden group to store the base objects for block definitions
    m_blockDefinitionGroup = static_cast<App::DocumentObjectGroup*>(
        document->addObject("App::DocumentObjectGroup", "_BlockDefinitions")
    );
    m_blockDefinitionGroup->Visibility.setValue(false);
    // Create a hidden group to store unreferenced blocks
    m_unreferencedBlocksGroup = static_cast<App::DocumentObjectGroup*>(
        document->addObject("App::DocumentObjectGroup", "_UnreferencedBlocks")
    );
    m_unreferencedBlocksGroup->Visibility.setValue(false);
}

bool ImpExpDxfRead::ReadEntitiesSection()
{
    // After parsing the BLOCKS section, compose all block definitions
    // into FreeCAD objects before processing the ENTITIES section.
    ComposeBlocks();

    DrawingEntityCollector collector(*this);
    if (m_importMode == ImportMode::FusedShapes) {
        std::map<CDxfRead::CommonEntityAttributes, std::list<TopoDS_Shape>> ShapesToCombine;
        {
            ShapeSavingEntityCollector savingCollector(*this, ShapesToCombine);
            if (!CDxfRead::ReadEntitiesSection()) {
                return false;
            }
        }

        // Merge the contents of ShapesToCombine and AddObject the result(s)
        // TODO: We do end-to-end joining or complete merging as selected by the options.
        for (auto& shapeSet : ShapesToCombine) {
            m_entityAttributes = shapeSet.first;
            CombineShapes(
                shapeSet.second,
                m_entityAttributes.m_Layer == nullptr ? "Compound"
                                                      : m_entityAttributes.m_Layer->Name.c_str()
            );
        }
    }
    else {
        if (!CDxfRead::ReadEntitiesSection()) {
            return false;
        }
    }
    if (m_preserveLayers) {
        for (auto& layerEntry : Layers) {
            ((Layer*)layerEntry.second)->FinishLayer();
        }
    }
    return true;
}

void ImpExpDxfRead::CombineShapes(std::list<TopoDS_Shape>& shapes, const char* nameBase) const
{
    BRep_Builder builder;
    TopoDS_Compound comp;
    builder.MakeCompound(comp);
    for (const auto& sh : shapes) {
        if (!sh.IsNull()) {
            builder.Add(comp, sh);
        }
    }
    if (!comp.IsNull()) {
        Collector->AddObject(comp, nameBase);
    }
}

TopoDS_Shape ImpExpDxfRead::CombineShapesToCompound(const std::list<TopoDS_Shape>& shapes) const
{
    if (shapes.empty()) {
        return TopoDS_Shape();
    }
    BRep_Builder builder;
    TopoDS_Compound comp;
    builder.MakeCompound(comp);
    for (const auto& sh : shapes) {
        if (!sh.IsNull()) {
            builder.Add(comp, sh);
        }
    }
    return comp;
}

void ImpExpDxfRead::setOptions()
{
    ParameterGrp::handle hGrp = App::GetApplication().GetParameterGroupByPath(
        getOptionSource().c_str()
    );
    m_stats.importSettings.clear();

    m_preserveLayers = hGrp->GetBool("dxfUseDraftVisGroups", true);
    m_stats.importSettings["Use layers"] = m_preserveLayers ? "Yes" : "No";

    m_preserveColors = hGrp->GetBool("dxfGetOriginalColors", true);
    m_stats.importSettings["Use colors from the DXF file"] = m_preserveColors ? "Yes" : "No";

    // Read the new master import mode parameter, set the default.
    int mode = hGrp->GetInt("DxfImportMode", static_cast<int>(ImportMode::IndividualShapes));
    m_importMode = static_cast<ImportMode>(mode);

    // TODO: joingeometry should give an intermediate between MergeShapes and SingleShapes which
    // will merge shapes that happen to join end-to-end. As such it should be in the radio button
    // set, except that the legacy importer can do joining either for sketches or for shapes. What
    // this really means is there should be an "Import as sketch" checkbox, and only the
    // MergeShapes, JoinShapes, and SingleShapes radio buttons should be allowed, i.e. Draft Objects
    // would be ignored.
    // Update: The "Join geometry" option is now a checkbox that is only enabled for the legacy
    // importer. Whether the modern importer should support this is still up for debate.
    bool joinGeometry = hGrp->GetBool("joingeometry", false);
    m_stats.importSettings["Join geometry"] = joinGeometry ? "Yes" : "No";

    double scaling = hGrp->GetFloat("dxfScaling", 1.0);
    SetAdditionalScaling(scaling);
    m_stats.importSettings["Manual scaling factor"] = std::to_string(scaling);

    m_importAnnotations = hGrp->GetBool("dxftext", false);
    m_stats.importSettings["Import texts and dimensions"] = m_importAnnotations ? "Yes" : "No";

    m_importPoints = hGrp->GetBool("dxfImportPoints", true);
    m_stats.importSettings["Import points"] = m_importPoints ? "Yes" : "No";

    m_importPaperSpaceEntities = hGrp->GetBool("dxflayout", false);
    m_stats.importSettings["Import layout objects"] = m_importPaperSpaceEntities ? "Yes" : "No";

    m_importHiddenBlocks = hGrp->GetBool("dxfstarblocks", false);
    m_stats.importSettings["Import hidden blocks"] = m_importHiddenBlocks ? "Yes" : "No";

    // TODO: There is currently no option for this: m_importFrozenLayers =
    // hGrp->GetBool("dxffrozenLayers", false);
    // TODO: There is currently no option for this: m_importHiddenLayers =
    // hGrp->GetBool("dxfhiddenLayers", true);
}

void ImpExpDxfRead::ComposeFlattenedBlock(const std::string& blockName, std::set<std::string>& composed)
{
    // 1. Base Case: If already composed, do nothing.
    if (composed.count(blockName)) {
        return;
    }

    // 2. Find the raw block data.
    auto it = this->Blocks.find(blockName);
    if (it == this->Blocks.end()) {
        ImportError("Block '%s' is referenced but not defined. Skipping.", blockName.c_str());
        return;
    }
    const Block& blockData = it->second;

    // 3. Collect all geometry shapes for this block.
    std::list<TopoDS_Shape> shapeCollection;

    // 4. Process primitive geometry.
    for (const auto& [attributes, builderList] : blockData.GeometryBuilders) {
        for (const auto& builder : builderList) {
            shapeCollection.push_back(builder.shape);
        }
    }

    // 5. Process nested inserts recursively.
    for (const auto& insertAttrPair : blockData.Inserts) {
        for (const auto& nestedInsert : insertAttrPair.second) {
            // Ensure the nested block is composed first.
            ComposeFlattenedBlock(nestedInsert.Name, composed);
            // Mark the nested block as referenced so it's not moved to the "Unreferenced" group.
            m_referencedBlocks.insert(nestedInsert.Name);

            // Retrieve the final, flattened shape of the nested block.
            auto shape_it = m_flattenedBlockShapes.find(nestedInsert.Name);
            if (shape_it != m_flattenedBlockShapes.end()) {
                if (!shape_it->second.IsNull()) {
                    // Use the Part::TopoShape wrapper to access the transformShape method.
                    Part::TopoShape nestedShape(shape_it->second);
                    // Apply the insert's transformation.
                    Base::Placement pl(
                        nestedInsert.Point,
                        Base::Rotation(Base::Vector3d(0, 0, 1), nestedInsert.Rotation)
                    );
                    Base::Matrix4D transform = pl.toMatrix();
                    transform.scale(nestedInsert.Scale);
                    nestedShape.transformShape(transform, true, true);  // Use copy=true
                    shapeCollection.push_back(nestedShape.getShape());
                }
            }
        }
    }

    // 6. Build the final merged shape.
    TopoDS_Shape finalShape = CombineShapesToCompound(shapeCollection);
    m_flattenedBlockShapes[blockName] = finalShape;  // Cache the result.

    // 7. Create the final Part::Feature object.
    if (!finalShape.IsNull()) {
        std::string featureName = "BLOCK_" + blockName;
        auto blockFeature = document->addObject<Part::Feature>(
            document->getUniqueObjectName(featureName.c_str()).c_str()
        );
        blockFeature->Shape.setValue(finalShape);
        blockFeature->Visibility.setValue(false);
        m_blockDefinitionGroup->addObject(blockFeature);
        this->m_blockDefinitions[blockName] = blockFeature;
    }

    // 8. Mark this block as composed.
    composed.insert(blockName);
}

void ImpExpDxfRead::ComposeParametricBlock(const std::string& blockName, std::set<std::string>& composed)
{
    // 1. Base Case: If this block has already been composed, we're done.
    if (composed.count(blockName)) {
        return;
    }

    // 2. Find the raw block data from the parsing phase.
    auto it = this->Blocks.find(blockName);
    if (it == this->Blocks.end()) {
        ImportError("Block '%s' is referenced but not defined. Skipping.", blockName.c_str());
        return;
    }
    const Block& blockData = it->second;

    // 3. Create the master Part::Compound for this block definition.
    std::string compName = "BLOCK_" + blockName;
    auto blockCompound = document->addObject<Part::Compound>(
        document->getUniqueObjectName(compName.c_str()).c_str()
    );
    m_blockDefinitionGroup->addObject(blockCompound);
    IncrementCreatedObjectCount();
    blockCompound->Visibility.setValue(false);
    this->m_blockDefinitions[blockName] = blockCompound;

    std::vector<App::DocumentObject*> childObjects;

    // 4. Recursively Compose and Link Nested Inserts.
    for (const auto& insertAttrPair : blockData.Inserts) {
        for (const auto& nestedInsert : insertAttrPair.second) {
            // Ensure the dependency is composed before we try to link to it.
            ComposeParametricBlock(nestedInsert.Name, composed);
            // Mark the nested block as referenced so it's not moved to the "Unreferenced" group.
            m_referencedBlocks.insert(nestedInsert.Name);

            // Create the App::Link for this nested insert.
            auto baseObjIt = m_blockDefinitions.find(nestedInsert.Name);
            if (baseObjIt != m_blockDefinitions.end()) {
                // The link's name should be based on the block it is inserting, not the parent.
                std::string linkName = "Link_" + nestedInsert.Name;
                auto link = document->addObject<App::Link>(
                    document->getUniqueObjectName(linkName.c_str()).c_str()
                );
                link->setLink(-1, baseObjIt->second);
                link->LinkTransform.setValue(false);

                // Apply placement and scale to the link itself.
                Base::Placement pl(
                    nestedInsert.Point,
                    Base::Rotation(Base::Vector3d(0, 0, 1), nestedInsert.Rotation)
                );
                link->Placement.setValue(pl);
                link->ScaleVector.setValue(nestedInsert.Scale);
                link->Visibility.setValue(false);
                IncrementCreatedObjectCount();
                childObjects.push_back(link);
            }
        }
    }

    // 5. Create and Link Primitive Geometry from the collected builders.
    for (const auto& [attributes, builderList] : blockData.GeometryBuilders) {
        this->m_entityAttributes = attributes;  // Set attributes for layer/color handling

        for (const auto& builder : builderList) {
            App::DocumentObject* newObject = nullptr;
            switch (builder.type) {
                // Existing cases for other primitives
                case GeometryBuilder::PrimitiveType::Line: {
                    newObject = createLinePrimitive(TopoDS::Edge(builder.shape), document, "Line");
                    break;
                }
                case GeometryBuilder::PrimitiveType::Point: {
                    newObject = createVertexPrimitive(TopoDS::Vertex(builder.shape), document, "Point");
                    break;
                }
                case GeometryBuilder::PrimitiveType::Circle:
                case GeometryBuilder::PrimitiveType::Arc: {
                    const char* name = (builder.type == GeometryBuilder::PrimitiveType::Circle)
                        ? "Circle"
                        : "Arc";
                    auto* p = createCirclePrimitive(TopoDS::Edge(builder.shape), document, name);
                    if (!p) {
                        break;
                    }
                    if (builder.type == GeometryBuilder::PrimitiveType::Circle) {
                        p->Angle1.setValue(0.0);
                        p->Angle2.setValue(360.0);
                    }
                    newObject = p;
                    break;
                }
                case GeometryBuilder::PrimitiveType::Ellipse: {
                    newObject
                        = createEllipsePrimitive(TopoDS::Edge(builder.shape), document, "Ellipse");
                    break;
                }
                case GeometryBuilder::PrimitiveType::Spline: {
                    // Splines are generic Part::Feature as no Part primitive exists
                    auto* p = document->addObject<Part::Feature>("Spline");
                    p->Shape.setValue(builder.shape);
                    newObject = p;
                    break;
                }
                case GeometryBuilder::PrimitiveType::PolylineFlattened: {
                    // This creates a simple Part::Feature wrapping the wire, which is standard for
                    // block children.
                    newObject = createFlattenedPolylineFeature(TopoDS::Wire(builder.shape), "Polyline");
                    break;
                }
                case GeometryBuilder::PrimitiveType::PolylineParametric: {
                    // This creates a Part::Compound containing line/arc segments.
                    newObject
                        = createParametricPolylineCompound(TopoDS::Wire(builder.shape), "Polyline");
                    // No styling needed here, as the block's instance will control appearance.
                    break;
                }
                case GeometryBuilder::PrimitiveType::None:  // Default/fallback if not handled
                default: {
                    // Generic shape, e.g., 3DFACE
                    newObject = createGenericShapeFeature(builder.shape, document, "Shape");
                    break;
                }
            }

            if (newObject) {
                IncrementCreatedObjectCount();
                newObject->Visibility.setValue(false);  // Children of blocks are hidden by default
                // Layer and color are applied by the block itself (Part::Compound) or its children
                // if overridden.
                ApplyGuiStyles(static_cast<Part::Feature*>(newObject));  // Apply style to the child
                                                                         // object
                childObjects.push_back(newObject);  // Add to the block's main children list
            }
        }
    }

    // 6. Finalize the Part::Compound.
    if (!childObjects.empty()) {
        blockCompound->Links.setValues(childObjects);
    }

    // 7. Mark this block as composed.
    composed.insert(blockName);
}

void ImpExpDxfRead::ComposeBlocks()
{
    std::set<std::string> composedBlocks;

    if (m_importMode == ImportMode::FusedShapes) {
        // User wants flattened geometry for performance.
        for (const auto& pair : this->Blocks) {
            if (composedBlocks.find(pair.first) == composedBlocks.end()) {
                ComposeFlattenedBlock(pair.first, composedBlocks);
            }
        }
    }
    else {
        // User wants a parametric, editable structure.
        for (const auto& pair : this->Blocks) {
            if (composedBlocks.find(pair.first) == composedBlocks.end()) {
                ComposeParametricBlock(pair.first, composedBlocks);
            }
        }
    }
}

void ImpExpDxfRead::FinishImport()
{
    // This function runs after all blocks have been parsed and composed.
    // It sorts all created block definitions into two groups: those that are
    // actively referenced in the drawing, and those that are not.

    std::vector<App::DocumentObject*> referenced;
    std::vector<App::DocumentObject*> unreferenced;

    for (const auto& pair : m_blockDefinitions) {
        const std::string& blockName = pair.first;
        App::DocumentObject* blockObj = pair.second;

        bool is_referenced = (m_referencedBlocks.find(blockName) != m_referencedBlocks.end());

        // A block is considered "referenced" if it was explicitly inserted
        // or if it is an anonymous system block (e.g., for dimensions).
        // All other named blocks are considered unreferenced if not found in the set.
        if (is_referenced || (blockName.rfind('*', 0) == 0)) {
            referenced.push_back(blockObj);
        }
        else {
            unreferenced.push_back(blockObj);
        }
    }

    // Re-assign the group contents by setting the PropertyLinkList for each group.
    // This correctly re-parents the objects in the document's dependency graph.
    m_blockDefinitionGroup->Group.setValues(referenced);
    m_unreferencedBlocksGroup->Group.setValues(unreferenced);

    // Final cleanup: If the unreferenced group is empty, remove it to avoid
    // unnecessary clutter in the document tree. Otherwise, ensure it's hidden.
    if (unreferenced.empty()) {
        try {
            document->removeObject(m_unreferencedBlocksGroup->getNameInDocument());
        }
        catch (const Base::Exception& e) {
            // It's not critical if removal fails, but we should log it.
            e.reportException();
        }
    }
    else {
        m_unreferencedBlocksGroup->Visibility.setValue(false);
    }

    // If no blocks were defined in the file at all, remove the main definitions
    // group as well to keep the document clean.
    if (m_blockDefinitionGroup && m_blockDefinitionGroup->Group.getValues().empty()) {
        try {
            document->removeObject(m_blockDefinitionGroup->getNameInDocument());
        }
        catch (const Base::Exception& e) {
            e.reportException();
        }
    }

    // call the base class implementation if it has one
    CDxfRead::FinishImport();
}

bool ImpExpDxfRead::OnReadBlock(const std::string& name, int flags)
{
    // Step 1: Check for external references first. This is a critical check.
    if ((flags & 0x04) != 0) {  // Block is an Xref
        UnsupportedFeature("External (xref) BLOCK");
        return SkipBlockContents();
    }

    // Step 2: Check if the block is anonymous/system.
    bool isAnonymous = (name.find('*') == 0);
    if (isAnonymous) {
        if (name.size() > 1) {
            char type = std::toupper(name[1]);
            if (type == 'D') {
                m_stats.systemBlockCounts["Dimension-related (*D)"]++;
            }
            else if (type == 'H' || type == 'X') {
                m_stats.systemBlockCounts["Hatch-related (*H, *X)"]++;
            }
            else {
                m_stats.systemBlockCounts["Other System Blocks"]++;
            }
        }
        else {
            m_stats.systemBlockCounts["Other System Blocks"]++;
        }

        if (!m_importHiddenBlocks) {
            return SkipBlockContents();
        }
    }
    else {
        m_stats.entityCounts["BLOCK"]++;
    }

    // Step 3: Check for duplicates to prevent errors.
    if (this->Blocks.count(name)) {
        ImportError("Duplicate block name '%s' found. Ignoring subsequent definition.", name.c_str());
        return SkipBlockContents();
    }

    // Step 4: Use the temporary Block struct and Collector to parse all contents into memory.
    // The .emplace method is slightly more efficient here.
    auto& temporaryBlock = Blocks.emplace(std::make_pair(name, Block(name, flags))).first->second;
    BlockDefinitionCollector blockCollector(
        *this,
        temporaryBlock.GeometryBuilders,
        temporaryBlock.Inserts
    );
    if (!ReadBlockContents()) {
        return false;  // Abort on parsing error
    }

    // That's it. The block is now parsed into this->Blocks.
    // Composition will happen later in ComposeBlocks().
    return true;
}

// --- The remaining ImpExpDxfRead callback methods (OnRead*, DrawingEntityCollector,
// --- Layer, etc.) are in ImpExpDxfCallbacks.cpp.
// --- The ImpExpDxfWrite methods and getStatsAsPyObject are in ImpExpDxfWrite.cpp.
// --- This split works around MSVC 2019 internal compiler error (ICE) in the code generator
// --- (p2/main.c line 213) which crashes on overly large translation units.
