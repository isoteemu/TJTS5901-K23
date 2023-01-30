"""
JYU TJTS5901 Course project
===========================
"""

from importlib_metadata import (PackageNotFoundError,
                                version)

from .app import create_app

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = [
    "create_app",
    "__version__",
]
