# SPDX-License-Identifier: LGPL-2.1-or-later
# **************************************************************************
#   Copyright (c) 2026 FreeCAD contributors
#
#   Python ABC layer for the PDM provider interface (D13 – PDM provider
#   interface).  New PDM integrations should subclass PdmProviderBase and
#   register via FreeCAD.setActivePdmProvider(instance).
#
#   The C++ PdmProvider interface (src/App/PdmProvider.h) defines the
#   contract for native providers.  This ABC mirrors the same contract for
#   Python-level providers so that scripted integrations (e.g. Git, SVN,
#   cloud vaults) can be loaded without a C++ build step.
# **************************************************************************

"""PDM (Product Data Management) provider Python interface.

Usage::

    from App.PdmProviderPy import PdmProviderBase
    import FreeCAD

    class GitPdmProvider(PdmProviderBase):
        def name(self) -> str:
            return "Git PDM"

        def check_out(self, file_path: str) -> bool:
            import subprocess
            result = subprocess.run(["git", "add", file_path])
            return result.returncode == 0
        # … implement remaining abstract methods …

    FreeCAD.setActivePdmProvider(GitPdmProvider())
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import List


@dataclass
class PdmRevision:
    """A single revision entry in the PDM history."""

    revision_id: str = ""
    author: str = ""
    timestamp: str = ""   # ISO 8601
    comment: str = ""


class PdmProviderBase(abc.ABC):
    """Abstract base class for FreeCAD PDM provider plug-ins.

    Subclass this and override **all** abstract methods.  After instantiating
    your provider, register it with::

        FreeCAD.setActivePdmProvider(provider_instance)

    Only one provider is active at a time for a given FreeCAD session.
    """

    # ── Identity ────────────────────────────────────────────────────

    @abc.abstractmethod
    def name(self) -> str:
        """Return a short human-readable name, e.g. "Git PDM" or "Vault"."""

    # ── File lifecycle ──────────────────────────────────────────────

    @abc.abstractmethod
    def check_out(self, file_path: str) -> bool:
        """Check out *file_path* for exclusive editing.

        Return ``True`` on success.
        """

    @abc.abstractmethod
    def check_in(self, file_path: str, comment: str) -> bool:
        """Check in *file_path* with revision *comment*.

        Return ``True`` on success.
        """

    @abc.abstractmethod
    def undo_check_out(self, file_path: str) -> bool:
        """Discard local edits and revert to the latest server version.

        Return ``True`` on success.
        """

    # ── Query ───────────────────────────────────────────────────────

    @abc.abstractmethod
    def get_revision(self, file_path: str) -> str:
        """Return the current revision string for *file_path*."""

    @abc.abstractmethod
    def get_history(self, file_path: str) -> List[PdmRevision]:
        """Return the complete revision history for *file_path*."""

    @abc.abstractmethod
    def is_checked_out(self, file_path: str) -> bool:
        """Return ``True`` if *file_path* is currently checked out by anyone."""

    @abc.abstractmethod
    def locked_by(self, file_path: str) -> str:
        """Return the username that holds the lock, or an empty string."""

    # ── Locking ─────────────────────────────────────────────────────

    @abc.abstractmethod
    def lock(self, file_path: str) -> bool:
        """Acquire an exclusive lock on *file_path*."""

    @abc.abstractmethod
    def unlock(self, file_path: str) -> bool:
        """Release the lock on *file_path*."""

    @abc.abstractmethod
    def get_latest(self, file_path: str) -> bool:
        """Retrieve the latest version of *file_path* from the server."""

    # ── Optional hooks ──────────────────────────────────────────────
    # Subclasses may override these to receive lifecycle events from
    # FreeCAD.  The default implementations are no-ops.

    def on_document_opened(self, file_path: str) -> None:
        """Called after FreeCAD opens *file_path*."""

    def on_document_saved(self, file_path: str) -> None:
        """Called after FreeCAD saves *file_path*."""

    def on_document_closed(self, file_path: str) -> None:
        """Called when FreeCAD closes the document for *file_path*."""


# ---------------------------------------------------------------------------
# Module-level provider registry
# ---------------------------------------------------------------------------

_active_provider: PdmProviderBase | None = None


def get_active_provider() -> PdmProviderBase | None:
    """Return the currently registered PDM provider, or ``None``."""
    return _active_provider


def set_active_provider(provider: PdmProviderBase) -> None:
    """Register *provider* as the active PDM integration for this session.

    Raises :exc:`TypeError` if *provider* is not a :class:`PdmProviderBase`
    instance.
    """
    if not isinstance(provider, PdmProviderBase):
        raise TypeError(
            f"Expected a PdmProviderBase instance, got {type(provider).__name__!r}"
        )
    global _active_provider
    _active_provider = provider
