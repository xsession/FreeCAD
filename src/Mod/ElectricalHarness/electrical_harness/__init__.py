"""Namespace package for Electrical Harness workbench internals."""

from pathlib import Path

_pkg_dir = Path(__file__).resolve().parent
_parent_dir = str(_pkg_dir.parent)
if _parent_dir not in __path__:
    __path__.append(_parent_dir)
