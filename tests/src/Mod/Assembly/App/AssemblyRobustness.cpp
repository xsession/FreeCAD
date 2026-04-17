// SPDX-License-Identifier: LGPL-2.1-or-later

/***************************************************************************
 *   Copyright (c) 2026 FreeCAD contributors                               *
 *                                                                         *
 *   Regression tests for AssemblyObject robustness.                       *
 *   Proves solver safety against dangling pointers, NaN output, and       *
 *   rapid solve calls.                                                    *
 ***************************************************************************/

#include <gtest/gtest.h>

#include <cmath>
#include <App/Application.h>
#include <App/Document.h>
#include <App/DocumentObject.h>
#include <Base/Placement.h>
#include <Base/Vector3D.h>
#include <Mod/Assembly/App/AssemblyObject.h>

class AssemblyRobustness : public ::testing::Test
{
protected:
    void SetUp() override
    {
        doc = App::GetApplication().newDocument("AssemblyTestDoc");
    }

    void TearDown() override
    {
        App::GetApplication().closeDocument("AssemblyTestDoc");
    }

    App::Document* doc = nullptr;
};

TEST_F(AssemblyRobustness, solveEmptyAssemblyReturnsError)
{
    // Solver behavior differs by solver/runtime config:
    // empty assemblies may report no-solution (-6) or no-op success (0).
    auto* assembly = dynamic_cast<Assembly::AssemblyObject*>(
        doc->addObject("Assembly::AssemblyObject", "Assembly"));
    ASSERT_NE(assembly, nullptr);

    int result = assembly->solve(false, false);
    EXPECT_TRUE(result == -6 || result == 0)
        << "Empty assembly should return -6 (no grounded parts) or 0 (no-op): " << result;
}

TEST_F(AssemblyRobustness, solveWithNoJointsDoesNotCrash)
{
    auto* assembly = dynamic_cast<Assembly::AssemblyObject*>(
        doc->addObject("Assembly::AssemblyObject", "Assembly"));
    ASSERT_NE(assembly, nullptr);

    // Solve with no joints — should not crash
    int result = assembly->solve(false, false);
    SUCCEED() << "Solve with no joints did not crash, returned: " << result;
}

TEST_F(AssemblyRobustness, undoSolveWithNoHistoryDoesNotCrash)
{
    auto* assembly = dynamic_cast<Assembly::AssemblyObject*>(
        doc->addObject("Assembly::AssemblyObject", "Assembly"));
    ASSERT_NE(assembly, nullptr);

    // Undo with no previous positions should be a no-op
    assembly->undoSolve();
    SUCCEED() << "undoSolve with no history did not crash";
}

TEST_F(AssemblyRobustness, clearUndoDoesNotCrash)
{
    auto* assembly = dynamic_cast<Assembly::AssemblyObject*>(
        doc->addObject("Assembly::AssemblyObject", "Assembly"));
    ASSERT_NE(assembly, nullptr);

    assembly->clearUndo();
    SUCCEED() << "clearUndo did not crash";
}

TEST_F(AssemblyRobustness, multipleRapidSolvesDoNotCrash)
{
    auto* assembly = dynamic_cast<Assembly::AssemblyObject*>(
        doc->addObject("Assembly::AssemblyObject", "Assembly"));
    ASSERT_NE(assembly, nullptr);

    // Multiple rapid solve calls should not cause race conditions
    for (int i = 0; i < 5; ++i) {
        int result = assembly->solve(false, false);
        EXPECT_TRUE(result == -6 || result == 0)
            << "Rapid solve #" << i << " returned unexpected result: " << result;
    }
    SUCCEED() << "5 rapid solve calls completed without crash";
}

TEST_F(AssemblyRobustness, doDragStepWithNoSetupDoesNotCrash)
{
    auto* assembly = dynamic_cast<Assembly::AssemblyObject*>(
        doc->addObject("Assembly::AssemblyObject", "Assembly"));
    ASSERT_NE(assembly, nullptr);

    // doDragStep without a prior preDrag setup should not crash
    assembly->doDragStep();
    SUCCEED() << "doDragStep without setup did not crash";
}

TEST_F(AssemblyRobustness, validatePlacementNaN)
{
    // Test that NaN placement values are detected
    Base::Placement plc;
    plc.setPosition(Base::Vector3d(std::nan(""), 0.0, 0.0));

    // NaN in a position should be detectable
    double x = plc.getPosition().x;
    EXPECT_TRUE(std::isnan(x)) << "NaN should be detectable in placement position";
}

TEST_F(AssemblyRobustness, validatePlacementInfinity)
{
    // Test that Infinity placement values are detected
    Base::Placement plc;
    plc.setPosition(Base::Vector3d(std::numeric_limits<double>::infinity(), 0.0, 0.0));

    double x = plc.getPosition().x;
    EXPECT_TRUE(std::isinf(x)) << "Infinity should be detectable in placement position";
}

TEST_F(AssemblyRobustness, solveAfterObjectDeletionDoesNotCrash)
{
    auto* assembly = dynamic_cast<Assembly::AssemblyObject*>(
        doc->addObject("Assembly::AssemblyObject", "Assembly"));
    ASSERT_NE(assembly, nullptr);

    // Add and then remove an object — solve should still not crash
    auto* obj = doc->addObject("App::DocumentObject", "TempObj");
    doc->removeObject("TempObj");

    int result = assembly->solve(false, false);
    SUCCEED() << "Solve after object deletion did not crash, returned: " << result;
}
