"""
Undetected Geckodriver
======================
This package provides a sophisticated wrapper around the
webdriver.Firefox class from the Selenium package. It
attempts to avoid detection by web services by patching
certain parts of the Firefox browser.

Original author: Bytexenon (https://github.com/Bytexenon)
Fork maintainer: LunarWatcher (https://github.com/LunarWatcher
"""

# Imports #
import importlib.metadata

from .driver import Firefox  # noqa
from .errors import (
    FirefoxCopyException,
    FirefoxNotFoundException,
    FirefoxPatchException,
)

# Constants #
try:
    __version__ = importlib.metadata.version("undetected-geckodriver-lw")
except Exception:
    __version__ = "<unknown; not installed via pip>"


__all__ = [
    "Firefox",
    "FirefoxNotFoundException",
    "FirefoxCopyException",
    "FirefoxPatchException",
]
