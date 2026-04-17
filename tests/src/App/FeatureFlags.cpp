// SPDX-License-Identifier: LGPL-2.1-or-later

#include <gtest/gtest.h>

#include <App/FeatureFlags.h>

#include <src/App/InitApplication.h>

class FeatureFlagsTest : public ::testing::Test
{
protected:
    static void SetUpTestSuite()
    {
        tests::initApplication();
    }

    void TearDown() override
    {
        App::FeatureFlags::clearAllOverrides();
    }
};

TEST_F(FeatureFlagsTest, DefaultValueWhenNoOverrideNoPreference)
{
    // Unknown flag with explicit default
    EXPECT_FALSE(App::FeatureFlags::isEnabled("NonExistentFlag", false));
    EXPECT_TRUE(App::FeatureFlags::isEnabled("NonExistentFlag", true));
}

TEST_F(FeatureFlagsTest, OverrideEnabled)
{
    App::FeatureFlags::setOverride("TestFlag", true);
    EXPECT_TRUE(App::FeatureFlags::isEnabled("TestFlag", false));
}

TEST_F(FeatureFlagsTest, OverrideDisabled)
{
    App::FeatureFlags::setOverride("TestFlag", false);
    EXPECT_FALSE(App::FeatureFlags::isEnabled("TestFlag", true));
}

TEST_F(FeatureFlagsTest, ClearOverrideRevertsToDefault)
{
    App::FeatureFlags::setOverride("TestFlag", true);
    EXPECT_TRUE(App::FeatureFlags::isEnabled("TestFlag", false));

    App::FeatureFlags::clearOverride("TestFlag");
    EXPECT_FALSE(App::FeatureFlags::isEnabled("TestFlag", false));
}

TEST_F(FeatureFlagsTest, ClearAllOverrides)
{
    App::FeatureFlags::setOverride("Flag1", true);
    App::FeatureFlags::setOverride("Flag2", true);

    App::FeatureFlags::clearAllOverrides();

    EXPECT_FALSE(App::FeatureFlags::isEnabled("Flag1", false));
    EXPECT_FALSE(App::FeatureFlags::isEnabled("Flag2", false));
}

TEST_F(FeatureFlagsTest, KnownFlagDefaults)
{
    // SketchAutoConstrain defaults to true in the known flags table
    EXPECT_TRUE(App::FeatureFlags::isEnabled(App::FeatureFlagDefs::SketchAutoConstrain));
    // ParallelRecompute defaults to false
    EXPECT_FALSE(App::FeatureFlags::isEnabled(App::FeatureFlagDefs::ParallelRecompute));
}

TEST_F(FeatureFlagsTest, AllFlagsReturnsKnownFlags)
{
    auto all = App::FeatureFlags::allFlags();
    EXPECT_GT(all.size(), 0u);
    EXPECT_TRUE(all.count(App::FeatureFlagDefs::ParallelRecompute) > 0);
    EXPECT_TRUE(all.count(App::FeatureFlagDefs::RestAPI) > 0);
}

TEST_F(FeatureFlagsTest, OverrideTakesPrecedenceOverPreference)
{
    // Even if preference says true, override to false wins
    App::FeatureFlags::setOverride(App::FeatureFlagDefs::SketchAutoConstrain, false);
    EXPECT_FALSE(App::FeatureFlags::isEnabled(App::FeatureFlagDefs::SketchAutoConstrain));
}
