"""
A GUI application for geochronology, focussed on calculating disequilibrium
U-Pb ages.

Notes
-----
Some parts of the source code, including this file, are inspired by  the
crispy application written by Marius Retegan of the European Synchrotron Radiation
Facility and released under an MIT licence.
see: https://github.com/mretegan/crispy

"""
__version__ = "0.1.1"

import os
import sys

version = __version__
debug = 0

# https://stackoverflow.com/questions/7674790/bundling-data-files-with-pyinstaller-onefile
def resourceAbsolutePath(relativePath):
    """Get the absolute path to a resource. Works for development and for PyInstaller."""
    basePath = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(basePath, relativePath)