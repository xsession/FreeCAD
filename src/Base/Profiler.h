// SPDX-License-Identifier: LGPL-2.1-or-later
/****************************************************************************
 *                                                                          *
 *   Copyright (c) 2025 Joao Matos <joao@tritao.eu>                         *
 *                                                                          *
 *   This file is part of FreeCAD.                                          *
 *                                                                          *
 *   FreeCAD is free software: you can redistribute it and/or modify it     *
 *   under the terms of the GNU Lesser General Public License as            *
 *   published by the Free Software Foundation, either version 2.1 of the   *
 *   License, or (at your option) any later version.                        *
 *                                                                          *
 *   FreeCAD is distributed in the hope that it will be useful, but         *
 *   WITHOUT ANY WARRANTY; without even the implied warranty of             *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU       *
 *   Lesser General Public License for more details.                        *
 *                                                                          *
 *   You should have received a copy of the GNU Lesser General Public       *
 *   License along with FreeCAD. If not, see                                *
 *   <https://www.gnu.org/licenses/>.                                       *
 *                                                                          *
 ***************************************************************************/

#ifdef TRACY_ENABLE
# include <tracy/Tracy.hpp>
#else
# define TracyNoop

# define ZoneNamed(x, y)
# define ZoneNamedN(x, y, z)
# define ZoneNamedC(x, y, z)
# define ZoneNamedNC(x, y, z, w)

# define ZoneTransient(x, y)
# define ZoneTransientN(x, y, z)

# define ZoneScoped
# define ZoneScopedN(x)
# define ZoneScopedC(x)
# define ZoneScopedNC(x, y)

# define ZoneText(x, y)
# define ZoneTextV(x, y, z)
# define ZoneTextF(x, ...)
# define ZoneTextVF(x, y, ...)
# define ZoneName(x, y)
# define ZoneNameV(x, y, z)
# define ZoneNameF(x, ...)
# define ZoneNameVF(x, y, ...)
# define ZoneColor(x)
# define ZoneColorV(x, y)
# define ZoneValue(x)
# define ZoneValueV(x, y)
# define ZoneIsActive false
# define ZoneIsActiveV(x) false

# define FrameMark
# define FrameMarkNamed(x)
# define FrameMarkStart(x)
# define FrameMarkEnd(x)

# define FrameImage(x, y, z, w, a)

# define TracyLockable(type, varname) type varname
# define TracyLockableN(type, varname, desc) type varname
# define TracySharedLockable(type, varname) type varname
# define TracySharedLockableN(type, varname, desc) type varname
# define LockableBase(type) type
# define SharedLockableBase(type) type
# define LockMark(x) (void)x
# define LockableName(x, y, z)

# define TracyPlot(x, y)
# define TracyPlotConfig(x, y, z, w, a)

# define TracyMessage(x, y)
# define TracyMessageL(x)
# define TracyMessageC(x, y, z)
# define TracyMessageLC(x, y)
# define TracyAppInfo(x, y)

# define TracyAlloc(x, y)
# define TracyFree(x)
# define TracyMemoryDiscard(x)
# define TracySecureAlloc(x, y)
# define TracySecureFree(x)
# define TracySecureMemoryDiscard(x)

# define TracyAllocN(x, y, z)
# define TracyFreeN(x, y)
# define TracySecureAllocN(x, y, z)
# define TracySecureFreeN(x, y)

# define ZoneNamedS(x, y, z)
# define ZoneNamedNS(x, y, z, w)
# define ZoneNamedCS(x, y, z, w)
# define ZoneNamedNCS(x, y, z, w, a)

# define ZoneTransientS(x, y, z)
# define ZoneTransientNS(x, y, z, w)

# define ZoneScopedS(x)
# define ZoneScopedNS(x, y)
# define ZoneScopedCS(x, y)
# define ZoneScopedNCS(x, y, z)

# define TracyAllocS(x, y, z)
# define TracyFreeS(x, y)
# define TracyMemoryDiscardS(x, y)
# define TracySecureAllocS(x, y, z)
# define TracySecureFreeS(x, y)
# define TracySecureMemoryDiscardS(x, y)

# define TracyAllocNS(x, y, z, w)
# define TracyFreeNS(x, y, z)
# define TracySecureAllocNS(x, y, z, w)
# define TracySecureFreeNS(x, y, z)

# define TracyMessageS(x, y, z)
# define TracyMessageLS(x, y)
# define TracyMessageCS(x, y, z, w)
# define TracyMessageLCS(x, y, z)

# define TracySourceCallbackRegister(x, y)
# define TracyParameterRegister(x, y)
# define TracyParameterSetup(x, y, z, w)
# define TracyIsConnected false
# define TracyIsStarted false
# define TracySetProgramName(x)

# define TracyFiberEnter(x)
# define TracyFiberEnterHint(x, y)
# define TracyFiberLeave
#endif

// ── FreeCAD convenience profiling macros ────────────────────────────────
//
// These macros provide a stable FreeCAD-specific profiling API.
// When Tracy is enabled, they delegate to Tracy's ZoneScoped macros.
// When FREECAD_ENABLE_PROFILING is defined (without Tracy), they use a
// lightweight chronometer that logs to Base::Console for > 0.1ms scopes.
// In release builds with neither flag, they compile to nothing.
//
// Usage:
//   void expensiveOperation() {
//       FREECAD_PROFILE_SCOPE("ExpensiveOp");
//       // ... code ...
//   }

#ifdef TRACY_ENABLE

#define FREECAD_PROFILE_SCOPE(name)     ZoneScopedN(name)
#define FREECAD_PROFILE_FUNCTION()      ZoneScoped
#define FREECAD_PROFILE_FRAME(name)     FrameMarkNamed(name)
#define FREECAD_PROFILE_VALUE(name, v)  TracyPlot(name, static_cast<double>(v))

#elif defined(FREECAD_ENABLE_PROFILING)

#include <Base/Console.h>
#include <chrono>

namespace Base
{

/// RAII scope timer — logs elapsed time to Console on destruction.
class ProfileScope
{
public:
    explicit ProfileScope(const char* scopeName)
        : scopeName(scopeName)
        , start(std::chrono::steady_clock::now())
    {}

    ~ProfileScope()
    {
        auto end = std::chrono::steady_clock::now();
        auto us  = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
        if (us > 100) {  // Only log if > 0.1ms to reduce noise
            Base::Console().Log("[Profile] %s: %lld us\n",
                                scopeName, static_cast<long long>(us));
        }
    }

    ProfileScope(const ProfileScope&) = delete;
    ProfileScope& operator=(const ProfileScope&) = delete;

private:
    const char* scopeName;
    std::chrono::steady_clock::time_point start;
};

}  // namespace Base

#define FREECAD_PROF_CONCAT2(a, b) a##b
#define FREECAD_PROF_CONCAT(a, b)  FREECAD_PROF_CONCAT2(a, b)

#define FREECAD_PROFILE_SCOPE(name) \
    ::Base::ProfileScope FREECAD_PROF_CONCAT(_fc_prof_, __LINE__)(name)
#define FREECAD_PROFILE_FUNCTION()      FREECAD_PROFILE_SCOPE(__FUNCTION__)
#define FREECAD_PROFILE_FRAME(name)     ((void)0)
#define FREECAD_PROFILE_VALUE(name, v)  ((void)0)

#else  // Release — no-op

#define FREECAD_PROFILE_SCOPE(name)     ((void)0)
#define FREECAD_PROFILE_FUNCTION()      ((void)0)
#define FREECAD_PROFILE_FRAME(name)     ((void)0)
#define FREECAD_PROFILE_VALUE(name, v)  ((void)0)

#endif
