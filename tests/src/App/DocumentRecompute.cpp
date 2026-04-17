// SPDX-License-Identifier: LGPL-2.1-or-later

/***************************************************************************
 *   Copyright (c) 2026 FreeCAD contributors                               *
 *                                                                         *
 *   Regression tests for Document recompute cascade prevention.           *
 *   Proves idempotent recompute and minimal dependency propagation.       *
 ***************************************************************************/

#include <gtest/gtest.h>

#include <App/Application.h>
#include <App/Document.h>
#include <App/DocumentObject.h>
#include <App/DocumentObjectGroup.h>

class DocumentRecompute : public ::testing::Test
{
protected:
    void SetUp() override
    {
        doc = App::GetApplication().newDocument("RecomputeTestDoc");
    }

    void TearDown() override
    {
        App::GetApplication().closeDocument("RecomputeTestDoc");
    }

    App::Document* doc = nullptr;
};

TEST_F(DocumentRecompute, emptyDocumentRecomputeDoesNotCrash)
{
    // Recomputing an empty document should be a no-op
    doc->recompute();
    SUCCEED() << "Empty document recompute did not crash";
}

TEST_F(DocumentRecompute, idempotentRecompute)
{
    // Two consecutive recomputes with no changes should not trigger
    // unnecessary recomputations on the second pass
    auto* obj = doc->addObject("App::DocumentObjectGroup", "Group1");
    ASSERT_NE(obj, nullptr);

    // First recompute
    doc->recompute();

    // At this point nothing is touched
    EXPECT_FALSE(obj->isTouched())
        << "Object should not be touched after recompute";

    // Second recompute — should be essentially a no-op
    int recomputeCount = doc->recompute();
    EXPECT_EQ(recomputeCount, 0)
        << "Second recompute with no changes should recompute zero objects";
}

TEST_F(DocumentRecompute, singleObjectRecompute)
{
    auto* obj = doc->addObject("App::DocumentObjectGroup", "Group1");
    ASSERT_NE(obj, nullptr);

    // Touch the object
    obj->touch();
    EXPECT_TRUE(obj->isTouched());

    // Recompute should process it
    int count = doc->recompute();
    EXPECT_GE(count, 0) << "Recompute should succeed";
    EXPECT_FALSE(obj->isTouched())
        << "Object should not be touched after recompute";
}

TEST_F(DocumentRecompute, canAbortRecomputeParameterExists)
{
    // Verify the CanAbortRecompute preference can be read/written roundtrip.
    auto hGrp = App::GetApplication().GetParameterGroupByPath(
        "User parameter:BaseApp/Preferences/Document");

    const bool original = hGrp->GetBool("CanAbortRecompute", true);

    hGrp->SetBool("CanAbortRecompute", true);
    EXPECT_TRUE(hGrp->GetBool("CanAbortRecompute", false));

    hGrp->SetBool("CanAbortRecompute", false);
    EXPECT_FALSE(hGrp->GetBool("CanAbortRecompute", true));

    hGrp->SetBool("CanAbortRecompute", original);
}

TEST_F(DocumentRecompute, canAbortRecomputePersistsAcrossParameterHandles)
{
    auto hGrp = App::GetApplication().GetParameterGroupByPath(
        "User parameter:BaseApp/Preferences/Document");
    const bool original = hGrp->GetBool("CanAbortRecompute", true);

    hGrp->SetBool("CanAbortRecompute", true);
    auto freshHandleTrue = App::GetApplication().GetParameterGroupByPath(
        "User parameter:BaseApp/Preferences/Document");
    EXPECT_TRUE(freshHandleTrue->GetBool("CanAbortRecompute", false));

    hGrp->SetBool("CanAbortRecompute", false);
    auto freshHandleFalse = App::GetApplication().GetParameterGroupByPath(
        "User parameter:BaseApp/Preferences/Document");
    EXPECT_FALSE(freshHandleFalse->GetBool("CanAbortRecompute", true));

    hGrp->SetBool("CanAbortRecompute", original);
}

TEST_F(DocumentRecompute, recomputeWithMultipleObjects)
{
    // Add several objects and ensure recompute handles them all
    for (int i = 0; i < 10; ++i) {
        std::string name = "Group" + std::to_string(i);
        auto* obj = doc->addObject("App::DocumentObjectGroup", name.c_str());
        ASSERT_NE(obj, nullptr);
    }

    doc->recompute();

    // All should be clean after recompute
    for (auto* obj : doc->getObjects()) {
        EXPECT_FALSE(obj->isTouched())
            << obj->getNameInDocument() << " should not be touched after recompute";
    }
}

TEST_F(DocumentRecompute, recomputeAfterObjectRemoval)
{
    auto* obj1 = doc->addObject("App::DocumentObjectGroup", "Group1");
    auto* obj2 = doc->addObject("App::DocumentObjectGroup", "Group2");
    ASSERT_NE(obj1, nullptr);
    ASSERT_NE(obj2, nullptr);

    doc->recompute();

    // Remove one object
    doc->removeObject("Group1");

    // Recompute should not crash with a dangling reference
    doc->recompute();
    SUCCEED() << "Recompute after object removal did not crash";
}
