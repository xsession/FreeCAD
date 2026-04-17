// SPDX-License-Identifier: LGPL-2.1-or-later
/***************************************************************************
 *   FreeCAD Public Plugin API – Stable Document Interface                 *
 *                                                                         *
 *   This header is part of the stable public API for FreeCAD plugins.     *
 *   Changes to this header follow semantic versioning and require an      *
 *   Architecture Decision Record (ADR).                                   *
 *                                                                         *
 *   API Version: 2.0                                                      *
 ***************************************************************************/

#pragma once

// Core document model
#include <App/Document.h>
#include <App/DocumentObject.h>
#include <App/Property.h>
#include <App/PropertyStandard.h>
#include <App/PropertyLinks.h>
#include <App/GeoFeature.h>
#include <App/FeatureCustom.h>
#include <App/FeaturePython.h>
#include <App/GroupExtension.h>
#include <App/GeoFeatureGroupExtension.h>

// Utilities
#include <App/Application.h>
#include <App/FeatureFlags.h>
#include <Base/Console.h>
#include <Base/Type.h>
#include <Base/Interpreter.h>
