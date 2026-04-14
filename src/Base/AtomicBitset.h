// SPDX-License-Identifier: LGPL-2.1-or-later

/***************************************************************************
 *   Copyright (c) 2026 FreeCAD contributors                              *
 *                                                                         *
 *   This file is part of FreeCAD.                                         *
 *                                                                         *
 *   FreeCAD is free software: you can redistribute it and/or modify it    *
 *   under the terms of the GNU Lesser General Public License as           *
 *   published by the Free Software Foundation, either version 2.1 of the  *
 *   License, or (at your option) any later version.                       *
 *                                                                         *
 *   FreeCAD is distributed in the hope that it will be useful, but        *
 *   WITHOUT ANY WARRANTY; without even the implied warranty of            *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU      *
 *   Lesser General Public License for more details.                       *
 *                                                                         *
 *   You should have received a copy of the GNU Lesser General Public      *
 *   License along with FreeCAD. If not, see                               *
 *   <https://www.gnu.org/licenses/>.                                      *
 *                                                                         *
 **************************************************************************/

#pragma once

#include <atomic>
#include <cstddef>
#include <cstdint>
#include <stdexcept>

namespace Base
{

/// A thread-safe replacement for std::bitset<32> using std::atomic<uint32_t>.
///
/// Provides the same test/set/reset/to_ulong interface as std::bitset<32> but
/// all operations are atomic (lock-free on all modern platforms).  This allows
/// concurrent readers and writers without external synchronization.
///
/// Drop-in replacement: code that calls .test(), .set(), .reset(), .to_ulong()
/// on a std::bitset<32> will compile unchanged against AtomicBitset.
class AtomicBitset
{
public:
    AtomicBitset() noexcept = default;

    explicit AtomicBitset(uint32_t value) noexcept
        : bits(value)
    {}

    // Allow copy/move (snapshot semantics — reads current value)
    AtomicBitset(const AtomicBitset& other) noexcept
        : bits(other.bits.load(std::memory_order_relaxed))
    {}
    AtomicBitset& operator=(const AtomicBitset& other) noexcept
    {
        if (this != &other) {
            bits.store(other.bits.load(std::memory_order_relaxed), std::memory_order_relaxed);
        }
        return *this;
    }

    // Assignment from raw value (for: StatusBits = decltype(StatusBits)(value))
    AtomicBitset& operator=(uint32_t value) noexcept
    {
        bits.store(value, std::memory_order_release);
        return *this;
    }

    /// Test whether bit at position \a pos is set.
    bool test(std::size_t pos) const
    {
        if (pos >= 32) {
            throw std::out_of_range("AtomicBitset::test: pos >= 32");
        }
        return (bits.load(std::memory_order_acquire) >> pos) & 1u;
    }

    /// Set bit at position \a pos to \a value.
    void set(std::size_t pos, bool value = true)
    {
        if (pos >= 32) {
            throw std::out_of_range("AtomicBitset::set: pos >= 32");
        }
        uint32_t mask = 1u << pos;
        if (value) {
            bits.fetch_or(mask, std::memory_order_release);
        }
        else {
            bits.fetch_and(~mask, std::memory_order_release);
        }
    }

    /// Reset (clear) bit at position \a pos.
    void reset(std::size_t pos)
    {
        set(pos, false);
    }

    /// Reset all bits.
    void reset() noexcept
    {
        bits.store(0u, std::memory_order_release);
    }

    /// Return the bits as an unsigned long.
    unsigned long to_ulong() const noexcept
    {
        return static_cast<unsigned long>(bits.load(std::memory_order_acquire));
    }

    /// Return the raw uint32_t value.
    uint32_t load(std::memory_order order = std::memory_order_acquire) const noexcept
    {
        return bits.load(order);
    }

    /// Store a raw uint32_t value.
    void store(uint32_t value, std::memory_order order = std::memory_order_release) noexcept
    {
        bits.store(value, order);
    }

    /// Atomically OR bits.
    uint32_t fetch_or(uint32_t mask,
                      std::memory_order order = std::memory_order_acq_rel) noexcept
    {
        return bits.fetch_or(mask, order);
    }

    /// Atomically AND bits.
    uint32_t fetch_and(uint32_t mask,
                       std::memory_order order = std::memory_order_acq_rel) noexcept
    {
        return bits.fetch_and(mask, order);
    }

private:
    std::atomic<uint32_t> bits{0};
};

}  // namespace Base
