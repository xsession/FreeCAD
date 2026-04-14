/***************************************************************************
 *   Copyright (c) 2026 FreeCAD contributors                              *
 *                                                                         *
 *   This file is part of the FreeCAD CAx development system.              *
 *                                                                         *
 *   This library is free software; you can redistribute it and/or         *
 *   modify it under the terms of the GNU Library General Public           *
 *   License as published by the Free Software Foundation; either          *
 *   version 2 of the License, or (at your option) any later version.      *
 *                                                                         *
 *   This library is distributed in the hope that it will be useful,       *
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
 *   GNU Library General Public License for more details.                  *
 *                                                                         *
 *   You should have received a copy of the GNU Library General Public     *
 *   License along with this library; see the file COPYING.LIB. If not,   *
 *   write to the Free Software Foundation, Inc., 59 Temple Place,         *
 *   Suite 330, Boston, MA  02111-1307, USA                                *
 *                                                                         *
 ***************************************************************************/

#pragma once

#include <Inventor/fields/SoSFBool.h>
#include <Inventor/fields/SoSFFloat.h>
#include <Inventor/fields/SoSFColor.h>
#include <Inventor/nodes/SoSeparator.h>

#include <FCGlobal.h>

class QOpenGLShaderProgram;
class QOpenGLFramebufferObject;

namespace Gui {

/**
 * SoFCPostProcessing — screen-space post-processing node.
 *
 * When placed at the END of the foreground root, it captures the depth buffer
 * written by the main scene and applies:
 *   1. SSAO  — Screen-Space Ambient Occlusion (contact shadows)
 *   2. Edge  — Silhouette/crease edge overlay via Sobel on depth + normals
 *
 * Both effects are screen-space, purely visual, and do not modify the scene
 * graph.  They are implemented as full-screen quad passes using GLSL shaders
 * compiled through Qt's QOpenGLShaderProgram.
 *
 * Designed for OpenGL 2.1 + GL_ARB_framebuffer_object (available on every
 * GPU since ~2008 and already required by FreeCAD's Coin3D backend).
 */
class GuiExport SoFCPostProcessing : public SoSeparator
{
    using inherited = SoSeparator;
    SO_NODE_HEADER(SoFCPostProcessing);

public:
    static void initClass();
    SoFCPostProcessing();

    // --- SSAO controls ---
    SoSFBool   enableSSAO;          // default TRUE
    SoSFFloat  ssaoRadius;          // world-space sample radius (default 0.5)
    SoSFFloat  ssaoIntensity;       // strength multiplier        (default 0.6)
    SoSFInt32  ssaoSamples;         // kernel size 8-64           (default 16)

    // --- Edge overlay controls ---
    SoSFBool   enableEdgeOverlay;   // default TRUE
    SoSFFloat  edgeThreshold;       // depth discontinuity threshold (default 0.002)
    SoSFFloat  edgeWidth;           // line width in pixels          (default 1.0)
    SoSFColor  edgeColor;           // silhouette edge color         (default black)

    // --- Bloom (Phase D) ---
    SoSFBool   enableBloom;         // default TRUE
    SoSFFloat  bloomIntensity;      // glow strength              (default 0.15)
    SoSFFloat  bloomThreshold;      // luminance cutoff           (default 0.7)

    // --- Vignette (Phase D) ---
    SoSFBool   enableVignette;      // default TRUE
    SoSFFloat  vignetteIntensity;   // edge darkening             (default 0.3)

    // --- Screen-Space Contact Shadows (Phase E) ---
    SoSFBool   enableShadows;       // default TRUE
    SoSFFloat  shadowDarkness;      // shadow strength 0-1        (default 0.35)

    // --- Contrast-Adaptive Sharpening (Phase E) ---
    SoSFBool   enableSharpening;    // default TRUE
    SoSFFloat  sharpenStrength;     // sharpening amount 0-1      (default 0.5)

    // --- Adaptive quality (Phase F) ---
    // When TRUE, the node is in "interactive" (navigation) mode and will
    // skip expensive passes (SSAO, bloom, shadows, sharpening) to maintain
    // smooth framerate.  Only cheap passes (edges, vignette) are kept for
    // spatial orientation.  Set to FALSE to render at full quality.
    SoSFBool   interactiveMode;     // default FALSE

    void GLRender(SoGLRenderAction* action) override;

protected:
    ~SoFCPostProcessing() override;

private:
    struct Private;
    Private* d;

    void initGL();
    void resizeFBO(int w, int h);
    void resizeBloomFBOs(int w, int h);
    void renderSSAO(int w, int h);
    void renderBloom(int w, int h);
    void renderComposite(int w, int h);
    void renderSharpen(int w, int h);
    void resizeCompositeFBO(int w, int h);
    void drawFullscreenQuad();
    bool checkGLCapabilities();
};

} // namespace Gui
