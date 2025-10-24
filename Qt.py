"""
Minimal Qt compatibility shim to run with PyQt5.

This provides the subset used by JsonStudio so we don't depend on the
external 'Qt.py' package at build time.
"""

from PyQt5 import QtWidgets, QtCore, QtGui, uic as _uic  # type: ignore

try:
    QtCore.Signal
except AttributeError:
    try:
        QtCore.Signal = QtCore.pyqtSignal
    except Exception:
        pass
try:
    QtCore.Slot
except AttributeError:
    try:
        QtCore.Slot = QtCore.pyqtSlot
    except Exception:
        pass


def _loadUi(path, baseinstance=None):
    """Load a .ui file using PyQt5.uic, matching the Qt.py API used here."""
    return _uic.loadUi(path, baseinstance)
