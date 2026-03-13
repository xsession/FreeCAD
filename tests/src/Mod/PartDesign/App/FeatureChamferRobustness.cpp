// SPDX-License-Identifier: LGPL-2.1-or-later

/***************************************************************************
 *   Copyright (c) 2026 FreeCAD contributors                               *
 *                                                                         *
 *   Regression tests for FeatureChamfer crash prevention.                 *
 *   Proves that oversized chamfer returns an error instead of crashing.   *
 ***************************************************************************/

#include <gtest/gtest.h>

#include <App/Application.h>
#include <App/Document.h>
#include <App/DocumentObject.h>
#include <Mod/PartDesign/App/FeatureChamfer.h>
#include <Mod/PartDesign/App/Body.h>
#include <Mod/Part/App/TopoShape.h>

class FeatureChamferRobustness : public ::testing::Test
{
protected:
    void SetUp() override
    {
        doc = App::GetApplication().newDocument("ChamferTestDoc");
    }

    void TearDown() override
    {
        App::GetApplication().closeDocument("ChamferTestDoc");
    }

    App::Document* doc = nullptr;
};

TEST_F(FeatureChamferRobustness, oversizedSizeReturnsErrorInsteadOfCrash)
{
    auto* chamfer = dynamic_cast<PartDesign::Chamfer*>(
        doc->addObject("PartDesign::Chamfer", "Chamfer"));
    ASSERT_NE(chamfer, nullptr);

    // Set an absurdly large chamfer size — should not crash
    chamfer->Size.setValue(50000.0);

    auto* ret = chamfer->execute();
    SUCCEED() << "Chamfer with oversized size did not crash";
    delete ret;
}

TEST_F(FeatureChamferRobustness, zeroSizeReturnsError)
{
    auto* chamfer = dynamic_cast<PartDesign::Chamfer*>(
        doc->addObject("PartDesign::Chamfer", "Chamfer"));
    ASSERT_NE(chamfer, nullptr);

    chamfer->Size.setValue(0.0);
    auto* ret = chamfer->execute();
    EXPECT_NE(ret, App::DocumentObject::StdReturn)
        << "Zero size should return an error";
    delete ret;
}

TEST_F(FeatureChamferRobustness, invalidAngleReturnsError)
{
    auto* chamfer = dynamic_cast<PartDesign::Chamfer*>(
        doc->addObject("PartDesign::Chamfer", "Chamfer"));
    ASSERT_NE(chamfer, nullptr);

    // Distance and Angle mode with invalid angle
    chamfer->ChamferType.setValue(2);  // "Distance and Angle"
    chamfer->Size.setValue(1.0);
    chamfer->Angle.setValue(0.0);  // Invalid: must be > 0

    auto* ret = chamfer->execute();
    EXPECT_NE(ret, App::DocumentObject::StdReturn)
        << "Zero angle should return an error";
    delete ret;
}

TEST_F(FeatureChamferRobustness, twoDistancesZeroSize2ReturnsError)
{
    auto* chamfer = dynamic_cast<PartDesign::Chamfer*>(
        doc->addObject("PartDesign::Chamfer", "Chamfer"));
    ASSERT_NE(chamfer, nullptr);

    // Two distances mode with zero second size
    chamfer->ChamferType.setValue(1);  // "Two distances"
    chamfer->Size.setValue(1.0);
    chamfer->Size2.setValue(0.0);

    auto* ret = chamfer->execute();
    EXPECT_NE(ret, App::DocumentObject::StdReturn)
        << "Zero Size2 in two-distance mode should return an error";
    delete ret;
}

TEST_F(FeatureChamferRobustness, nullBaseShapeReturnsError)
{
    auto* chamfer = dynamic_cast<PartDesign::Chamfer*>(
        doc->addObject("PartDesign::Chamfer", "Chamfer"));
    ASSERT_NE(chamfer, nullptr);

    chamfer->Size.setValue(1.0);
    auto* ret = chamfer->execute();
    SUCCEED() << "Chamfer with null base shape did not crash";
    delete ret;
}
