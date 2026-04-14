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

#include "PreCompiled.h"

#include "SoFCPostProcessing.h"

#include <Inventor/actions/SoGLRenderAction.h>
#include <Inventor/elements/SoViewportRegionElement.h>
#include <Inventor/elements/SoModelMatrixElement.h>
#include <Inventor/SbViewportRegion.h>

#include <QOpenGLShaderProgram>
#include <QOpenGLFramebufferObject>
#include <QOpenGLContext>
#include <QOpenGLFunctions>
#include <QOpenGLExtraFunctions>

#include <Base/Console.h>

#include <array>
#include <cmath>
#include <random>

#ifdef FC_OS_WIN32
#include <windows.h>
#endif

#ifdef FC_OS_MACOSX
#include <OpenGL/gl.h>
#else
#include <GL/gl.h>
#include <GL/glext.h>
#endif

using namespace Gui;

// ────────────────────────────────────────────────────────────────────
//  GLSL shader sources  (OpenGL 2.1 / GLSL 1.20 compatible)
// ────────────────────────────────────────────────────────────────────

// Vertex shader shared by both passes — draws a full-screen triangle
static const char* vsFullscreen = R"(
#version 120
attribute vec2 aPos;
varying vec2 vUV;
void main() {
    vUV = aPos * 0.5 + 0.5;
    gl_Position = vec4(aPos, 0.0, 1.0);
}
)";

// ──── SSAO fragment shader ────────────────────────────────────────
static const char* fsSSAO = R"(
#version 120
varying vec2 vUV;

uniform sampler2D uDepthTex;
uniform vec2      uTexelSize;   // 1.0 / resolution
uniform float     uRadius;      // sample radius in NDC
uniform float     uIntensity;   // AO strength
uniform int       uSamples;     // kernel size
uniform vec2      uKernel[64];  // Poisson-disk offsets
uniform float     uNear;
uniform float     uFar;

float linearizeDepth(float d) {
    // Reverse the standard OpenGL depth: z_ndc = 2*d - 1
    float z_ndc = 2.0 * d - 1.0;
    return (2.0 * uNear * uFar) / (uFar + uNear - z_ndc * (uFar - uNear));
}

void main() {
    float depth = texture2D(uDepthTex, vUV).r;
    if (depth >= 1.0) {
        // background — no occlusion
        gl_FragColor = vec4(1.0);
        return;
    }

    float centerZ = linearizeDepth(depth);
    float occlusion = 0.0;

    for (int i = 0; i < 64; ++i) {
        if (i >= uSamples) break;
        vec2 offset = uKernel[i] * uRadius;
        vec2 sampleUV = vUV + offset;

        // Clamp to valid texture coords
        sampleUV = clamp(sampleUV, vec2(0.0), vec2(1.0));

        float sampleDepth = texture2D(uDepthTex, sampleUV).r;
        float sampleZ = linearizeDepth(sampleDepth);

        // Range-aware occlusion: only count samples that are
        // within a reasonable depth range to avoid halos
        float rangeCheck = smoothstep(0.0, 1.0,
            uRadius * 500.0 / abs(centerZ - sampleZ));
        occlusion += (sampleZ < centerZ - 0.01 ? 1.0 : 0.0) * rangeCheck;
    }

    occlusion = 1.0 - (occlusion / float(uSamples)) * uIntensity;
    occlusion = clamp(occlusion, 0.0, 1.0);
    gl_FragColor = vec4(vec3(occlusion), 1.0);
}
)";

// ──── Composite fragment shader (Phase D+E: AO, edges, bloom, vignette, SSCS) ──
static const char* fsComposite = R"(
#version 120
varying vec2 vUV;

uniform sampler2D uColorTex;    // original scene color  (unit 0)
uniform sampler2D uDepthTex;    // depth buffer          (unit 1)
uniform sampler2D uSSAOTex;     // SSAO occlusion factor (unit 2)
uniform sampler2D uBloomTex;    // bloom glow            (unit 3)

uniform vec2      uTexelSize;
uniform float     uNear;
uniform float     uFar;

// Edge params
uniform int       uEnableEdges;
uniform float     uThreshold;
uniform float     uEdgeWidth;
uniform vec3      uEdgeColor;

// Phase D params
uniform float     uBloomIntensity;
uniform float     uVignetteIntensity;

// Phase E: Screen-Space Contact Shadows
uniform int       uEnableShadows;
uniform float     uShadowDarkness;

float linearizeDepth(float d) {
    float z_ndc = 2.0 * d - 1.0;
    return (2.0 * uNear * uFar) / (uFar + uNear - z_ndc * (uFar - uNear));
}

// Screen-space contact shadows: march from this pixel toward the light
// in screen space and check for occluding geometry.
// Light direction is upper-right in screen space (camera-relative lighting).
float contactShadow(vec2 uv, float fragZ) {
    // March direction: toward upper-right (matching fill light direction)
    vec2 marchDir = normalize(vec2(0.45, 0.75));
    float stepPx = 2.0;  // pixels per step
    float occlusion = 0.0;

    for (int i = 1; i <= 16; ++i) {
        vec2 offset = marchDir * stepPx * float(i) * uTexelSize;
        vec2 sampleUV = uv + offset;

        // Bounds check
        if (sampleUV.x < 0.001 || sampleUV.x > 0.999 ||
            sampleUV.y < 0.001 || sampleUV.y > 0.999) break;

        float sampleRaw = texture2D(uDepthTex, sampleUV).r;
        if (sampleRaw >= 1.0) continue;  // background

        float sampleZ = linearizeDepth(sampleRaw);
        float depthDiff = fragZ - sampleZ;

        // Geometry closer to camera within a reasonable thickness → occluder
        float thickness = fragZ * 0.05;
        if (depthDiff > fragZ * 0.001 && depthDiff < thickness) {
            // Soft falloff: closer march steps produce stronger shadows
            float fade = 1.0 - float(i) / 16.0;
            occlusion = max(occlusion, fade);
        }
    }

    return 1.0 - occlusion * uShadowDarkness;
}

void main() {
    vec3 color = texture2D(uColorTex, vUV).rgb;
    float depth = texture2D(uDepthTex, vUV).r;

    // Background pixels: add ground gradient + bloom
    if (depth >= 1.0) {
        vec3 bloom = texture2D(uBloomTex, vUV).rgb;
        // Ground gradient: subtle darkening in lower viewport (Inventor-style floor)
        float groundFade = smoothstep(0.0, 0.45, vUV.y);
        color *= mix(0.92, 1.0, groundFade);
        gl_FragColor = vec4(color + bloom * uBloomIntensity, 1.0);
        return;
    }

    float linearZ = linearizeDepth(depth);

    // Screen-space contact shadows
    if (uEnableShadows > 0) {
        float shadow = contactShadow(vUV, linearZ);
        // Warm shadow tint for Inventor-style light background
        vec3 shadowTint = mix(vec3(0.90, 0.89, 0.87), vec3(1.0), shadow);
        color *= shadowTint;
    }

    // Apply SSAO with warm tint in occluded areas (Inventor-style)
    float ao = texture2D(uSSAOTex, vUV).r;
    vec3 aoTint = mix(vec3(0.85, 0.84, 0.82), vec3(1.0), ao);
    color *= aoTint;

    // Edge detection (Sobel on linearized depth)
    if (uEnableEdges > 0) {
        vec2 ts = uTexelSize * uEdgeWidth;

        float d00 = linearizeDepth(texture2D(uDepthTex, vUV + vec2(-ts.x, -ts.y)).r);
        float d10 = linearizeDepth(texture2D(uDepthTex, vUV + vec2( 0.0,  -ts.y)).r);
        float d20 = linearizeDepth(texture2D(uDepthTex, vUV + vec2( ts.x, -ts.y)).r);
        float d01 = linearizeDepth(texture2D(uDepthTex, vUV + vec2(-ts.x,  0.0 )).r);
        float d21 = linearizeDepth(texture2D(uDepthTex, vUV + vec2( ts.x,  0.0 )).r);
        float d02 = linearizeDepth(texture2D(uDepthTex, vUV + vec2(-ts.x,  ts.y)).r);
        float d12 = linearizeDepth(texture2D(uDepthTex, vUV + vec2( 0.0,   ts.y)).r);
        float d22 = linearizeDepth(texture2D(uDepthTex, vUV + vec2( ts.x,  ts.y)).r);

        float gx = -d00 + d20 - 2.0*d01 + 2.0*d21 - d02 + d22;
        float gy = -d00 - 2.0*d10 - d20 + d02 + 2.0*d12 + d22;

        float edgeMag = sqrt(gx*gx + gy*gy) / max(linearZ, 0.01);
        float edgeFactor = smoothstep(uThreshold * 0.5, uThreshold, edgeMag);

        color = mix(color, uEdgeColor, edgeFactor);
    }

    // Bloom glow
    vec3 bloom = texture2D(uBloomTex, vUV).rgb;
    color += bloom * uBloomIntensity;

    // Vignette
    if (uVignetteIntensity > 0.0) {
        vec2 center = vUV - 0.5;
        float vignette = 1.0 - dot(center, center) * uVignetteIntensity * 2.0;
        color *= clamp(vignette, 0.0, 1.0);
    }

    gl_FragColor = vec4(clamp(color, 0.0, 1.0), 1.0);
}
)";

// ──── Bloom extraction fragment shader ────────────────────────────
static const char* fsBloomExtract = R"(
#version 120
varying vec2 vUV;

uniform sampler2D uColorTex;
uniform float     uThreshold;

void main() {
    vec3 color = texture2D(uColorTex, vUV).rgb;
    float lum = dot(color, vec3(0.2126, 0.7152, 0.0722));
    float contribution = max(lum - uThreshold, 0.0) / max(lum, 0.001);
    gl_FragColor = vec4(color * contribution, 1.0);
}
)";

// ──── Bloom blur fragment shader (9-tap separable Gaussian) ──────
static const char* fsBloomBlur = R"(
#version 120
varying vec2 vUV;

uniform sampler2D uBloomTex;
uniform vec2      uDirection;   // (1/w, 0) for H-pass; (0, 1/h) for V-pass

void main() {
    vec3 result = vec3(0.0);
    result += texture2D(uBloomTex, vUV - 4.0 * uDirection).rgb * 0.016216;
    result += texture2D(uBloomTex, vUV - 3.0 * uDirection).rgb * 0.054054;
    result += texture2D(uBloomTex, vUV - 2.0 * uDirection).rgb * 0.121621;
    result += texture2D(uBloomTex, vUV - 1.0 * uDirection).rgb * 0.194594;
    result += texture2D(uBloomTex, vUV                    ).rgb * 0.227027;
    result += texture2D(uBloomTex, vUV + 1.0 * uDirection).rgb * 0.194594;
    result += texture2D(uBloomTex, vUV + 2.0 * uDirection).rgb * 0.121621;
    result += texture2D(uBloomTex, vUV + 3.0 * uDirection).rgb * 0.054054;
    result += texture2D(uBloomTex, vUV + 4.0 * uDirection).rgb * 0.016216;
    gl_FragColor = vec4(result, 1.0);
}
)";

// ──── Contrast-Adaptive Sharpening (Phase E) ─────────────────────
// Modified unsharp mask with contrast-adaptive strength to avoid
// ringing on high-contrast edges while crisping soft details.
static const char* fsSharpen = R"(
#version 120
varying vec2 vUV;

uniform sampler2D uColorTex;
uniform vec2      uTexelSize;
uniform float     uSharpenStrength;

void main() {
    vec3 center = texture2D(uColorTex, vUV).rgb;
    vec3 top    = texture2D(uColorTex, vUV + vec2(0.0, -uTexelSize.y)).rgb;
    vec3 bottom = texture2D(uColorTex, vUV + vec2(0.0,  uTexelSize.y)).rgb;
    vec3 left   = texture2D(uColorTex, vUV + vec2(-uTexelSize.x, 0.0)).rgb;
    vec3 right  = texture2D(uColorTex, vUV + vec2( uTexelSize.x, 0.0)).rgb;

    // Local contrast: high contrast → less sharpening (avoid ringing)
    vec3 mn = min(center, min(min(top, bottom), min(left, right)));
    vec3 mx = max(center, max(max(top, bottom), max(left, right)));
    vec3 contrast = mx - mn;

    // Adaptive weight: inversely proportional to local contrast
    vec3 w = clamp(vec3(uSharpenStrength) / (contrast + 0.1), 0.0, 1.0) * 0.25;

    // Apply unsharp mask with adaptive weight
    vec3 blur = (top + bottom + left + right) * 0.25;
    vec3 detail = center - blur;
    vec3 sharpened = center + detail * w * 4.0;

    gl_FragColor = vec4(clamp(sharpened, 0.0, 1.0), 1.0);
}
)";

// ────────────────────────────────────────────────────────────────────
//  Private data
// ────────────────────────────────────────────────────────────────────

struct SoFCPostProcessing::Private
{
    bool initialized = false;
    bool capable = false;       // GL capabilities check result

    // Shaders
    QOpenGLShaderProgram* ssaoProgram = nullptr;
    QOpenGLShaderProgram* compositeProgram = nullptr;

    // FBO for SSAO intermediate result
    QOpenGLFramebufferObject* ssaoFBO = nullptr;
    int fboWidth = 0;
    int fboHeight = 0;

    // Depth texture captured from default framebuffer
    GLuint depthTex = 0;

    // SSAO kernel (Poisson disk)
    std::array<float, 128> kernel {};  // 64 vec2 = 128 floats

    // Phase D: color capture for composite pipeline
    GLuint colorTex = 0;

    // Phase D: bloom FBOs (half-resolution ping-pong)
    QOpenGLFramebufferObject* bloomFBO1 = nullptr;
    QOpenGLFramebufferObject* bloomFBO2 = nullptr;
    int bloomWidth = 0;
    int bloomHeight = 0;

    // Phase D: bloom shaders
    QOpenGLShaderProgram* bloomExtractProgram = nullptr;
    QOpenGLShaderProgram* bloomBlurProgram = nullptr;

    // Phase E: sharpening
    QOpenGLShaderProgram* sharpenProgram = nullptr;
    QOpenGLFramebufferObject* compositeFBO = nullptr;
    int compositeWidth = 0;
    int compositeHeight = 0;

    void generateKernel()
    {
        std::mt19937 rng(42); // deterministic seed for reproducibility
        std::uniform_real_distribution<float> dist(-1.0F, 1.0F);

        for (int i = 0; i < 64; ++i) {
            float x, y, len;
            do {
                x = dist(rng);
                y = dist(rng);
                len = x * x + y * y;
            } while (len > 1.0F || len < 0.0001F);
            // Scale samples to cluster near center (importance sampling)
            float scale = static_cast<float>(i) / 64.0F;
            scale = 0.1F + scale * scale * 0.9F;  // lerp(0.1, 1.0, scale^2)
            kernel[i * 2] = x * scale;
            kernel[i * 2 + 1] = y * scale;
        }
    }
};

// ────────────────────────────────────────────────────────────────────
//  Coin3D node setup
// ────────────────────────────────────────────────────────────────────

SO_NODE_SOURCE(SoFCPostProcessing)

void SoFCPostProcessing::initClass()
{
    SO_NODE_INIT_CLASS(SoFCPostProcessing, SoSeparator, "Separator");
}

SoFCPostProcessing::SoFCPostProcessing()
    : d(new Private)
{
    SO_NODE_CONSTRUCTOR(SoFCPostProcessing);

    SO_NODE_ADD_FIELD(enableSSAO,       (TRUE));
    SO_NODE_ADD_FIELD(ssaoRadius,       (0.5F));
    SO_NODE_ADD_FIELD(ssaoIntensity,    (0.6F));
    SO_NODE_ADD_FIELD(ssaoSamples,      (16));

    SO_NODE_ADD_FIELD(enableEdgeOverlay, (TRUE));
    SO_NODE_ADD_FIELD(edgeThreshold,     (0.002F));
    SO_NODE_ADD_FIELD(edgeWidth,         (1.0F));
    SO_NODE_ADD_FIELD(edgeColor,         (SbColor(0.18F, 0.18F, 0.20F)));  // Inventor-style charcoal

    // Phase D: Bloom & Vignette
    SO_NODE_ADD_FIELD(enableBloom,       (TRUE));
    SO_NODE_ADD_FIELD(bloomIntensity,    (0.15F));
    SO_NODE_ADD_FIELD(bloomThreshold,    (0.7F));
    SO_NODE_ADD_FIELD(enableVignette,    (TRUE));
    SO_NODE_ADD_FIELD(vignetteIntensity, (0.3F));

    // Phase E: Shadows & Sharpening
    SO_NODE_ADD_FIELD(enableShadows,     (TRUE));
    SO_NODE_ADD_FIELD(shadowDarkness,    (0.35F));
    SO_NODE_ADD_FIELD(enableSharpening,  (TRUE));
    SO_NODE_ADD_FIELD(sharpenStrength,   (0.5F));

    // Phase F: adaptive quality
    SO_NODE_ADD_FIELD(interactiveMode,   (FALSE));

    d->generateKernel();
}

SoFCPostProcessing::~SoFCPostProcessing()
{
    delete d->ssaoProgram;
    delete d->compositeProgram;
    delete d->bloomExtractProgram;
    delete d->bloomBlurProgram;
    delete d->sharpenProgram;
    delete d->ssaoFBO;
    delete d->bloomFBO1;
    delete d->bloomFBO2;
    delete d->compositeFBO;
    if (d->depthTex) {
        glDeleteTextures(1, &d->depthTex);
    }
    if (d->colorTex) {
        glDeleteTextures(1, &d->colorTex);
    }
    delete d;
}

// ────────────────────────────────────────────────────────────────────
//  GL capability check
// ────────────────────────────────────────────────────────────────────

bool SoFCPostProcessing::checkGLCapabilities()
{
    auto* ctx = QOpenGLContext::currentContext();
    if (!ctx) {
        return false;
    }

    auto* f = ctx->functions();
    if (!f) {
        return false;
    }

    // We need: framebuffers, GLSL shaders, and NPOT textures
    // All available since GL 2.0 which FreeCAD already requires
    if (!f->hasOpenGLFeature(QOpenGLFunctions::Framebuffers)) {
        Base::Console().Warning("SoFCPostProcessing: Framebuffers not supported\n");
        return false;
    }
    if (!f->hasOpenGLFeature(QOpenGLFunctions::Shaders)) {
        Base::Console().Warning("SoFCPostProcessing: Shaders not supported\n");
        return false;
    }
    return true;
}

// ────────────────────────────────────────────────────────────────────
//  Initialization (first use)
// ────────────────────────────────────────────────────────────────────

void SoFCPostProcessing::initGL()
{
    if (d->initialized) {
        return;
    }
    d->initialized = true;
    d->capable = checkGLCapabilities();
    if (!d->capable) {
        return;
    }

    // Compile SSAO shader
    d->ssaoProgram = new QOpenGLShaderProgram;
    bool ok = d->ssaoProgram->addShaderFromSourceCode(QOpenGLShader::Vertex, vsFullscreen);
    ok = ok && d->ssaoProgram->addShaderFromSourceCode(QOpenGLShader::Fragment, fsSSAO);
    d->ssaoProgram->bindAttributeLocation("aPos", 0);
    ok = ok && d->ssaoProgram->link();
    if (!ok) {
        Base::Console().Warning("SoFCPostProcessing: SSAO shader compilation failed: %s\n",
                                d->ssaoProgram->log().toUtf8().constData());
        d->capable = false;
        return;
    }

    // Compile composite (Phase D: full color replacement) shader
    d->compositeProgram = new QOpenGLShaderProgram;
    ok = d->compositeProgram->addShaderFromSourceCode(QOpenGLShader::Vertex, vsFullscreen);
    ok = ok && d->compositeProgram->addShaderFromSourceCode(QOpenGLShader::Fragment, fsComposite);
    d->compositeProgram->bindAttributeLocation("aPos", 0);
    ok = ok && d->compositeProgram->link();
    if (!ok) {
        Base::Console().Warning("SoFCPostProcessing: Composite shader compilation failed: %s\n",
                                d->compositeProgram->log().toUtf8().constData());
        d->capable = false;
        return;
    }

    // Compile bloom extraction shader
    d->bloomExtractProgram = new QOpenGLShaderProgram;
    ok = d->bloomExtractProgram->addShaderFromSourceCode(QOpenGLShader::Vertex, vsFullscreen);
    ok = ok && d->bloomExtractProgram->addShaderFromSourceCode(QOpenGLShader::Fragment, fsBloomExtract);
    d->bloomExtractProgram->bindAttributeLocation("aPos", 0);
    ok = ok && d->bloomExtractProgram->link();
    if (!ok) {
        Base::Console().Warning("SoFCPostProcessing: Bloom extract shader failed: %s\n",
                                d->bloomExtractProgram->log().toUtf8().constData());
        d->capable = false;
        return;
    }

    // Compile bloom blur shader
    d->bloomBlurProgram = new QOpenGLShaderProgram;
    ok = d->bloomBlurProgram->addShaderFromSourceCode(QOpenGLShader::Vertex, vsFullscreen);
    ok = ok && d->bloomBlurProgram->addShaderFromSourceCode(QOpenGLShader::Fragment, fsBloomBlur);
    d->bloomBlurProgram->bindAttributeLocation("aPos", 0);
    ok = ok && d->bloomBlurProgram->link();
    if (!ok) {
        Base::Console().Warning("SoFCPostProcessing: Bloom blur shader failed: %s\n",
                                d->bloomBlurProgram->log().toUtf8().constData());
        d->capable = false;
        return;
    }

    // Compile sharpening shader (Phase E)
    d->sharpenProgram = new QOpenGLShaderProgram;
    ok = d->sharpenProgram->addShaderFromSourceCode(QOpenGLShader::Vertex, vsFullscreen);
    ok = ok && d->sharpenProgram->addShaderFromSourceCode(QOpenGLShader::Fragment, fsSharpen);
    d->sharpenProgram->bindAttributeLocation("aPos", 0);
    ok = ok && d->sharpenProgram->link();
    if (!ok) {
        Base::Console().Warning("SoFCPostProcessing: Sharpen shader failed: %s\n",
                                d->sharpenProgram->log().toUtf8().constData());
        d->capable = false;
        return;
    }

    // Create a texture to hold a copy of the depth buffer
    glGenTextures(1, &d->depthTex);
    glBindTexture(GL_TEXTURE_2D, d->depthTex);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    glBindTexture(GL_TEXTURE_2D, 0);

    // Create a texture to hold a copy of the color buffer (Phase D)
    glGenTextures(1, &d->colorTex);
    glBindTexture(GL_TEXTURE_2D, d->colorTex);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    glBindTexture(GL_TEXTURE_2D, 0);
}

// ────────────────────────────────────────────────────────────────────
//  FBO management for SSAO intermediate buffer
// ────────────────────────────────────────────────────────────────────

void SoFCPostProcessing::resizeFBO(int w, int h)
{
    if (d->ssaoFBO && d->fboWidth == w && d->fboHeight == h) {
        return;
    }

    delete d->ssaoFBO;
    QOpenGLFramebufferObjectFormat fmt;
    fmt.setInternalTextureFormat(GL_RGBA8);
    d->ssaoFBO = new QOpenGLFramebufferObject(w, h, fmt);
    d->fboWidth = w;
    d->fboHeight = h;

    // Resize depth texture
    glBindTexture(GL_TEXTURE_2D, d->depthTex);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT24,
                 w, h, 0, GL_DEPTH_COMPONENT, GL_FLOAT, nullptr);
    glBindTexture(GL_TEXTURE_2D, 0);

    // Resize color texture (Phase D)
    glBindTexture(GL_TEXTURE_2D, d->colorTex);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8,
                 w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, nullptr);
    glBindTexture(GL_TEXTURE_2D, 0);
}

// ────────────────────────────────────────────────────────────────────
//  FBO management for bloom (half-resolution ping-pong)
// ────────────────────────────────────────────────────────────────────

void SoFCPostProcessing::resizeBloomFBOs(int w, int h)
{
    if (w <= 0 || h <= 0) {
        return;
    }
    if (d->bloomFBO1 && d->bloomWidth == w && d->bloomHeight == h) {
        return;
    }

    delete d->bloomFBO1;
    delete d->bloomFBO2;

    QOpenGLFramebufferObjectFormat fmt;
    fmt.setInternalTextureFormat(GL_RGBA8);
    d->bloomFBO1 = new QOpenGLFramebufferObject(w, h, fmt);
    d->bloomFBO2 = new QOpenGLFramebufferObject(w, h, fmt);
    d->bloomWidth = w;
    d->bloomHeight = h;
}

// ────────────────────────────────────────────────────────────────────
//  FBO management for composite intermediate (Phase E: sharpening)
// ────────────────────────────────────────────────────────────────────

void SoFCPostProcessing::resizeCompositeFBO(int w, int h)
{
    if (w <= 0 || h <= 0) {
        return;
    }
    if (d->compositeFBO && d->compositeWidth == w && d->compositeHeight == h) {
        return;
    }

    delete d->compositeFBO;

    QOpenGLFramebufferObjectFormat fmt;
    fmt.setInternalTextureFormat(GL_RGBA8);
    d->compositeFBO = new QOpenGLFramebufferObject(w, h, fmt);
    d->compositeWidth = w;
    d->compositeHeight = h;
}

// ────────────────────────────────────────────────────────────────────
//  Full-screen quad (triangle strip with 2 tris)
// ────────────────────────────────────────────────────────────────────

void SoFCPostProcessing::drawFullscreenQuad()
{
    // Use QOpenGLFunctions for GL 2.0+ vertex attrib calls (cross-platform)
    auto* f = QOpenGLContext::currentContext()->functions();

    static const float quad[] = {
       -1.0F, -1.0F,
        1.0F, -1.0F,
       -1.0F,  1.0F,
        1.0F,  1.0F
    };

    f->glEnableVertexAttribArray(0);
    f->glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, quad);
    glDrawArrays(GL_TRIANGLE_STRIP, 0, 4);
    f->glDisableVertexAttribArray(0);
}

// ────────────────────────────────────────────────────────────────────
//  SSAO pass — render to ssaoFBO
// ────────────────────────────────────────────────────────────────────

void SoFCPostProcessing::renderSSAO(int w, int h)
{
    auto* f = QOpenGLContext::currentContext()->functions();

    d->ssaoFBO->bind();

    glViewport(0, 0, w, h);
    glClearColor(1.0F, 1.0F, 1.0F, 1.0F);  // default = no occlusion
    glClear(GL_COLOR_BUFFER_BIT);

    d->ssaoProgram->bind();

    // Bind depth texture (unit 0)
    f->glActiveTexture(GL_TEXTURE0);
    glBindTexture(GL_TEXTURE_2D, d->depthTex);
    d->ssaoProgram->setUniformValue("uDepthTex", 0);

    d->ssaoProgram->setUniformValue("uTexelSize",
        1.0F / static_cast<float>(w), 1.0F / static_cast<float>(h));
    d->ssaoProgram->setUniformValue("uRadius", ssaoRadius.getValue());
    d->ssaoProgram->setUniformValue("uIntensity", ssaoIntensity.getValue());
    d->ssaoProgram->setUniformValue("uSamples", ssaoSamples.getValue());

    // Camera near/far — use reasonable defaults; exact values would need
    // to be extracted from the SoCamera. These work for typical CAD scenes.
    d->ssaoProgram->setUniformValue("uNear", 0.1F);
    d->ssaoProgram->setUniformValue("uFar", 10000.0F);

    // Upload kernel
    d->ssaoProgram->setUniformValueArray("uKernel",
        d->kernel.data(), 64, 2);

    drawFullscreenQuad();

    d->ssaoProgram->release();
    d->ssaoFBO->release();
}

// ────────────────────────────────────────────────────────────────────
//  Bloom pass — extract bright areas and blur (Phase D)
// ────────────────────────────────────────────────────────────────────

void SoFCPostProcessing::renderBloom(int w, int h)
{
    auto* f = QOpenGLContext::currentContext()->functions();
    int bw = std::max(1, w / 2);
    int bh = std::max(1, h / 2);

    resizeBloomFBOs(bw, bh);

    // Step 1: Extract bright areas from captured color → bloomFBO1
    d->bloomFBO1->bind();
    glViewport(0, 0, bw, bh);
    glClearColor(0.0F, 0.0F, 0.0F, 1.0F);
    glClear(GL_COLOR_BUFFER_BIT);

    d->bloomExtractProgram->bind();
    f->glActiveTexture(GL_TEXTURE0);
    glBindTexture(GL_TEXTURE_2D, d->colorTex);
    d->bloomExtractProgram->setUniformValue("uColorTex", 0);
    d->bloomExtractProgram->setUniformValue("uThreshold", bloomThreshold.getValue());
    drawFullscreenQuad();
    d->bloomExtractProgram->release();
    d->bloomFBO1->release();

    // Step 2: Horizontal Gaussian blur → bloomFBO2
    d->bloomFBO2->bind();
    glViewport(0, 0, bw, bh);
    glClear(GL_COLOR_BUFFER_BIT);

    d->bloomBlurProgram->bind();
    f->glActiveTexture(GL_TEXTURE0);
    glBindTexture(GL_TEXTURE_2D, d->bloomFBO1->texture());
    d->bloomBlurProgram->setUniformValue("uBloomTex", 0);
    d->bloomBlurProgram->setUniformValue("uDirection",
        1.0F / static_cast<float>(bw), 0.0F);
    drawFullscreenQuad();
    d->bloomBlurProgram->release();
    d->bloomFBO2->release();

    // Step 3: Vertical Gaussian blur → bloomFBO1
    d->bloomFBO1->bind();
    glViewport(0, 0, bw, bh);
    glClear(GL_COLOR_BUFFER_BIT);

    d->bloomBlurProgram->bind();
    f->glActiveTexture(GL_TEXTURE0);
    glBindTexture(GL_TEXTURE_2D, d->bloomFBO2->texture());
    d->bloomBlurProgram->setUniformValue("uBloomTex", 0);
    d->bloomBlurProgram->setUniformValue("uDirection",
        0.0F, 1.0F / static_cast<float>(bh));
    drawFullscreenQuad();
    d->bloomBlurProgram->release();
    d->bloomFBO1->release();
}

// ────────────────────────────────────────────────────────────────────
//  Final composite — write complete processed color to default FB
// ────────────────────────────────────────────────────────────────────

void SoFCPostProcessing::renderComposite(int w, int h)
{
    auto* f = QOpenGLContext::currentContext()->functions();

    d->compositeProgram->bind();

    // Unit 0: original scene color
    f->glActiveTexture(GL_TEXTURE0);
    glBindTexture(GL_TEXTURE_2D, d->colorTex);
    d->compositeProgram->setUniformValue("uColorTex", 0);

    // Unit 1: depth
    f->glActiveTexture(GL_TEXTURE1);
    glBindTexture(GL_TEXTURE_2D, d->depthTex);
    d->compositeProgram->setUniformValue("uDepthTex", 1);

    // Unit 2: SSAO
    f->glActiveTexture(GL_TEXTURE2);
    glBindTexture(GL_TEXTURE_2D, d->ssaoFBO->texture());
    d->compositeProgram->setUniformValue("uSSAOTex", 2);

    // Unit 3: bloom
    f->glActiveTexture(GL_TEXTURE3);
    glBindTexture(GL_TEXTURE_2D, d->bloomFBO1->texture());
    d->compositeProgram->setUniformValue("uBloomTex", 3);

    d->compositeProgram->setUniformValue("uTexelSize",
        1.0F / static_cast<float>(w), 1.0F / static_cast<float>(h));
    d->compositeProgram->setUniformValue("uNear", 0.1F);
    d->compositeProgram->setUniformValue("uFar", 10000.0F);

    // Edge params
    d->compositeProgram->setUniformValue("uEnableEdges",
        enableEdgeOverlay.getValue() ? 1 : 0);
    d->compositeProgram->setUniformValue("uThreshold", edgeThreshold.getValue());
    d->compositeProgram->setUniformValue("uEdgeWidth", edgeWidth.getValue());
    SbColor ec = edgeColor.getValue();
    d->compositeProgram->setUniformValue("uEdgeColor", ec[0], ec[1], ec[2]);

    // Phase D params — bloom intensity is 0 when disabled or in interactive mode
    //                  (SSAO and bloom FBOs are already cleared in those cases)
    bool interactive = interactiveMode.getValue();
    d->compositeProgram->setUniformValue("uBloomIntensity",
        (enableBloom.getValue() && !interactive) ? bloomIntensity.getValue() : 0.0F);
    d->compositeProgram->setUniformValue("uVignetteIntensity",
        enableVignette.getValue() ? vignetteIntensity.getValue() : 0.0F);

    // Phase E: shadow params — skip SSCS ray march in interactive mode
    bool shadowsOn = enableShadows.getValue() && !interactive;
    d->compositeProgram->setUniformValue("uEnableShadows",
        shadowsOn ? 1 : 0);
    d->compositeProgram->setUniformValue("uShadowDarkness",
        shadowsOn ? shadowDarkness.getValue() : 0.0F);

    drawFullscreenQuad();

    d->compositeProgram->release();
    f->glActiveTexture(GL_TEXTURE0);
}

// ────────────────────────────────────────────────────────────────────
//  Sharpening pass — reads compositeFBO, writes to default FB
// ────────────────────────────────────────────────────────────────────

void SoFCPostProcessing::renderSharpen(int w, int h)
{
    auto* f = QOpenGLContext::currentContext()->functions();

    d->sharpenProgram->bind();

    f->glActiveTexture(GL_TEXTURE0);
    glBindTexture(GL_TEXTURE_2D, d->compositeFBO->texture());
    d->sharpenProgram->setUniformValue("uColorTex", 0);

    d->sharpenProgram->setUniformValue("uTexelSize",
        1.0F / static_cast<float>(w), 1.0F / static_cast<float>(h));
    d->sharpenProgram->setUniformValue("uSharpenStrength",
        sharpenStrength.getValue());

    drawFullscreenQuad();

    d->sharpenProgram->release();
    f->glActiveTexture(GL_TEXTURE0);
}

// ────────────────────────────────────────────────────────────────────
//  GLRender override — called during scene traversal
// ────────────────────────────────────────────────────────────────────

void SoFCPostProcessing::GLRender(SoGLRenderAction* action)
{
    // Phase F: In interactive mode (navigation), skip all heavy passes.
    // Only edges + vignette survive (cheap composite-only pass) so the
    // user keeps spatial orientation at full framerate.
    bool interactive = interactiveMode.getValue();

    // Skip if all effects are disabled
    bool anyEffect = enableSSAO.getValue() || enableEdgeOverlay.getValue()
                   || enableBloom.getValue() || enableVignette.getValue()
                   || enableShadows.getValue() || enableSharpening.getValue();
    if (!anyEffect) {
        return;
    }

    // In interactive mode, only proceed if cheap effects are still on
    if (interactive) {
        bool anyCheapEffect = enableEdgeOverlay.getValue()
                            || enableVignette.getValue();
        if (!anyCheapEffect) {
            return;
        }
    }

    // Lazy init
    initGL();
    if (!d->capable) {
        return;
    }

    // Get viewport dimensions
    const SbViewportRegion& vp = SoViewportRegionElement::get(action->getState());
    SbVec2s vpSize = vp.getViewportSizePixels();
    int w = vpSize[0];
    int h = vpSize[1];
    if (w <= 0 || h <= 0) {
        return;
    }

    // Ensure FBO/texture are the right size
    resizeFBO(w, h);

    // ── Step 1: Capture current framebuffer ──
    glBindTexture(GL_TEXTURE_2D, d->depthTex);
    glCopyTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, 0, 0, w, h);
    glBindTexture(GL_TEXTURE_2D, 0);

    glBindTexture(GL_TEXTURE_2D, d->colorTex);
    glCopyTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, 0, 0, w, h);
    glBindTexture(GL_TEXTURE_2D, 0);

    // Save OpenGL state
    glPushAttrib(GL_ALL_ATTRIB_BITS);
    glDisable(GL_DEPTH_TEST);
    glDisable(GL_LIGHTING);
    glDepthMask(GL_FALSE);

    // ── Step 2: SSAO pass (skip in interactive mode — expensive) ──
    if (enableSSAO.getValue() && !interactive) {
        renderSSAO(w, h);
    }
    else {
        // Fill SSAO FBO with white (no occlusion)
        d->ssaoFBO->bind();
        glClearColor(1.0F, 1.0F, 1.0F, 1.0F);
        glClear(GL_COLOR_BUFFER_BIT);
        d->ssaoFBO->release();
    }

    // ── Step 3: Bloom passes (skip in interactive mode — expensive) ──
    if (enableBloom.getValue() && !interactive) {
        renderBloom(w, h);
    }
    else {
        // Ensure bloom FBOs exist and are cleared to black
        int bw = std::max(1, w / 2);
        int bh = std::max(1, h / 2);
        resizeBloomFBOs(bw, bh);
        d->bloomFBO1->bind();
        glClearColor(0.0F, 0.0F, 0.0F, 1.0F);
        glClear(GL_COLOR_BUFFER_BIT);
        d->bloomFBO1->release();
    }

    // ── Step 4: Final composite + optional sharpening ──
    glEnable(GL_BLEND);
    glBlendFunc(GL_ONE, GL_ZERO);  // dst = src (full replacement)

    glViewport(0, 0, w, h);
    glMatrixMode(GL_PROJECTION);
    glPushMatrix();
    glLoadIdentity();
    glMatrixMode(GL_MODELVIEW);
    glPushMatrix();
    glLoadIdentity();

    // In interactive mode, also skip shadows and sharpening
    bool sharpen = enableSharpening.getValue() && !interactive;

    if (sharpen) {
        // Composite → intermediate FBO, then sharpen → default FB
        resizeCompositeFBO(w, h);
        d->compositeFBO->bind();
        glViewport(0, 0, w, h);
        renderComposite(w, h);
        d->compositeFBO->release();

        glViewport(0, 0, w, h);
        renderSharpen(w, h);
    }
    else {
        // Composite directly to default FB
        renderComposite(w, h);
    }

    // Restore GL state
    glMatrixMode(GL_PROJECTION);
    glPopMatrix();
    glMatrixMode(GL_MODELVIEW);
    glPopMatrix();

    glPopAttrib();
}
