"""
Minimal Qt compatibility shim to run with PyQt5.

This provides the subset used by jsonStudio so we don't depend on the
external 'Qt.py' package at build time.
"""

from PyQt5 import QtWidgets, QtCore, QtGui, uic as _uic  # type: ignore


def _loadUi(path, baseinstance=None):
    """Load a .ui file using PyQt5.uic, matching the Qt.py API used here."""
    return _uic.loadUi(path, baseinstance)

