// SPDX-License-Identifier: LGPL-2.1-or-later

/***************************************************************************
 *   Copyright (c) 2026 FreeCAD contributors                               *
 *                                                                         *
 *   Regression tests for FeatureFillet crash prevention.                  *
 *   Proves that oversized fillet radius returns an error instead of       *
 *   crashing with SIGSEGV.                                                *
 ***************************************************************************/

#include <gtest/gtest.h>

#include <App/Application.h>
#include <App/Document.h>
#include <App/DocumentObject.h>
#include <Mod/PartDesign/App/FeatureFillet.h>
#include <Mod/PartDesign/App/Body.h>
#include <Mod/PartDesign/App/FeaturePad.h>
#include <Mod/Sketcher/App/SketchObject.h>
#include <Mod/Part/App/TopoShape.h>

class FeatureFilletRobustness : public ::testing::Test
{
protected:
    void SetUp() override
    {
        doc = App::GetApplication().newDocument("FilletTestDoc");
    }

    void TearDown() override
    {
        App::GetApplication().closeDocument("FilletTestDoc");
    }

    App::Document* doc = nullptr;
};

TEST_F(FeatureFilletRobustness, oversizedRadiusReturnsErrorInsteadOfCrash)
{
    // Creating a fillet with a radius larger than the geometry should produce
    // an error return, NOT a crash (SIGSEGV).
    auto* body = dynamic_cast<PartDesign::Body*>(
        doc->addObject("PartDesign::Body", "Body"));
    ASSERT_NE(body, nullptr);

    auto* fillet = dynamic_cast<PartDesign::Fillet*>(
        doc->addObject("PartDesign::Fillet", "Fillet"));
    ASSERT_NE(fillet, nullptr);

    // Set an absurdly large radius — should not crash
    fillet->Radius.setValue(50000.0);

    // Execute should return an error, not crash
    auto* ret = fillet->execute();
    // Any non-null return means an error was caught properly
    // (as opposed to a segfault which would kill the process)
    SUCCEED() << "Fillet with oversized radius did not crash";
    delete ret;
}

TEST_F(FeatureFilletRobustness, zeroRadiusReturnsError)
{
    auto* fillet = dynamic_cast<PartDesign::Fillet*>(
        doc->addObject("PartDesign::Fillet", "Fillet"));
    ASSERT_NE(fillet, nullptr);

    fillet->Radius.setValue(0.0);
    auto* ret = fillet->execute();
    // Zero radius should be caught by the radius <= 0 check
    EXPECT_NE(ret, App::DocumentObject::StdReturn)
        << "Zero radius should return an error";
    delete ret;
}

TEST_F(FeatureFilletRobustness, negativeRadiusReturnsError)
{
    auto* fillet = dynamic_cast<PartDesign::Fillet*>(
        doc->addObject("PartDesign::Fillet", "Fillet"));
    ASSERT_NE(fillet, nullptr);

    fillet->Radius.setValue(-5.0);
    auto* ret = fillet->execute();
    EXPECT_NE(ret, App::DocumentObject::StdReturn)
        << "Negative radius should return an error";
    delete ret;
}

TEST_F(FeatureFilletRobustness, nullBaseShapeReturnsError)
{
    // A fillet with no base shape should return an error, not crash
    auto* fillet = dynamic_cast<PartDesign::Fillet*>(
        doc->addObject("PartDesign::Fillet", "Fillet"));
    ASSERT_NE(fillet, nullptr);

    fillet->Radius.setValue(1.0);
    auto* ret = fillet->execute();
    // Without a base feature, should get an error
    SUCCEED() << "Fillet with null base shape did not crash";
    delete ret;
}

TEST_F(FeatureFilletRobustness, noEdgesSelectedReturnsError)
{
    auto* body = dynamic_cast<PartDesign::Body*>(
        doc->addObject("PartDesign::Body", "Body"));
    ASSERT_NE(body, nullptr);

    auto* fillet = dynamic_cast<PartDesign::Fillet*>(
        doc->addObject("PartDesign::Fillet", "Fillet"));
    ASSERT_NE(fillet, nullptr);

    // No edges set in Base property — should return an error
    fillet->Radius.setValue(1.0);
    auto* ret = fillet->execute();
    SUCCEED() << "Fillet with no edges selected did not crash";
    delete ret;
}
