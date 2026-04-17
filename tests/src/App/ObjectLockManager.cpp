// SPDX-License-Identifier: LGPL-2.1-or-later

#include <gtest/gtest.h>

#include <App/ObjectLockManager.h>

#include <sstream>
#include <thread>

class ObjectLockManagerTest : public ::testing::Test
{
protected:
    App::ObjectLockManager mgr;
};

// ── Collaborative lock tests ────────────────────────────────────────────

TEST_F(ObjectLockManagerTest, LockAndUnlock)
{
    EXPECT_TRUE(mgr.lockObject("Pad", "alice"));
    EXPECT_TRUE(mgr.isLocked("Pad"));
    EXPECT_EQ(mgr.lockedBy("Pad"), "alice");

    EXPECT_TRUE(mgr.unlockObject("Pad", "alice"));
    EXPECT_FALSE(mgr.isLocked("Pad"));
    EXPECT_EQ(mgr.lockedBy("Pad"), "");
}

TEST_F(ObjectLockManagerTest, IdempotentLockBySameUser)
{
    EXPECT_TRUE(mgr.lockObject("Pad", "alice"));
    EXPECT_TRUE(mgr.lockObject("Pad", "alice"));  // Same user → OK
    EXPECT_EQ(mgr.lockedBy("Pad"), "alice");
}

TEST_F(ObjectLockManagerTest, LockByDifferentUserFails)
{
    EXPECT_TRUE(mgr.lockObject("Pad", "alice"));
    EXPECT_FALSE(mgr.lockObject("Pad", "bob"));
    EXPECT_EQ(mgr.lockedBy("Pad"), "alice");
}

TEST_F(ObjectLockManagerTest, UnlockByWrongUserFails)
{
    EXPECT_TRUE(mgr.lockObject("Pad", "alice"));
    EXPECT_FALSE(mgr.unlockObject("Pad", "bob"));
    EXPECT_TRUE(mgr.isLocked("Pad"));
}

TEST_F(ObjectLockManagerTest, UnlockNonLockedIsIdempotent)
{
    EXPECT_TRUE(mgr.unlockObject("Pad", "anyone"));
}

TEST_F(ObjectLockManagerTest, IsLockedByOther)
{
    mgr.lockObject("Pad", "alice");
    EXPECT_TRUE(mgr.isLockedByOther("Pad", "bob"));
    EXPECT_FALSE(mgr.isLockedByOther("Pad", "alice"));
    EXPECT_FALSE(mgr.isLockedByOther("Fillet", "bob"));  // Not locked at all
}

TEST_F(ObjectLockManagerTest, AllLocksReturnsAll)
{
    mgr.lockObject("Pad", "alice");
    mgr.lockObject("Pocket", "bob");

    auto locks = mgr.allLocks();
    EXPECT_EQ(locks.size(), 2u);
}

TEST_F(ObjectLockManagerTest, ClearAllRemovesEverything)
{
    mgr.lockObject("Pad", "alice");
    mgr.lockObject("Pocket", "bob");
    mgr.clearAll();

    EXPECT_FALSE(mgr.isLocked("Pad"));
    EXPECT_FALSE(mgr.isLocked("Pocket"));
    EXPECT_EQ(mgr.allLocks().size(), 0u);
}

// ── Serialization tests ─────────────────────────────────────────────────

TEST_F(ObjectLockManagerTest, SaveAndLoadRoundTrip)
{
    mgr.lockObject("Pad", "alice");
    mgr.lockObject("Fillet", "bob");

    std::ostringstream os;
    mgr.saveLocks(os);
    std::string xml = os.str();

    // Verify XML structure
    EXPECT_NE(xml.find("<ObjectLocks"), std::string::npos);
    EXPECT_NE(xml.find("object=\"Pad\""), std::string::npos);
    EXPECT_NE(xml.find("owner=\"alice\""), std::string::npos);
    EXPECT_NE(xml.find("object=\"Fillet\""), std::string::npos);

    // Load into a fresh manager
    App::ObjectLockManager mgr2;
    mgr2.loadLocks(xml);

    EXPECT_EQ(mgr2.lockedBy("Pad"), "alice");
    EXPECT_EQ(mgr2.lockedBy("Fillet"), "bob");
    EXPECT_EQ(mgr2.allLocks().size(), 2u);
}

TEST_F(ObjectLockManagerTest, LoadEmptyXml)
{
    mgr.lockObject("Pad", "alice");
    mgr.loadLocks("");  // Should clear and load nothing
    EXPECT_EQ(mgr.allLocks().size(), 0u);
}

// ── Local (in-process) lock tests ───────────────────────────────────────

TEST_F(ObjectLockManagerTest, ReadLockDoesNotBlockOtherReads)
{
    // Two threads can acquire read locks simultaneously
    mgr.acquireRead("Pad");

    std::thread t([&]() {
        mgr.acquireRead("Pad");
        mgr.releaseRead("Pad");
    });
    t.join();

    mgr.releaseRead("Pad");
}

TEST_F(ObjectLockManagerTest, WriteLockIsExclusive)
{
    mgr.acquireWrite("Pad");

    bool acquired = false;
    std::thread t([&]() {
        // Try to acquire write — should block until released
        mgr.acquireWrite("Pad");
        acquired = true;
        mgr.releaseWrite("Pad");
    });

    // Brief pause to ensure thread is blocked
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
    EXPECT_FALSE(acquired);

    mgr.releaseWrite("Pad");
    t.join();

    EXPECT_TRUE(acquired);
}
