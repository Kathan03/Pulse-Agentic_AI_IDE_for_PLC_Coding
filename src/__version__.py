"""
Pulse IDE Version Information.

This file is the single source of truth for the Python backend version.
Keep this in sync with pulse-electron/package.json when releasing.
"""

__version__ = "0.1.0"
__version_info__ = tuple(int(x) for x in __version__.split("."))
