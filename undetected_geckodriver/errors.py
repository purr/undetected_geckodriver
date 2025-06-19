"""
Custom exceptions for undetected_geckodriver
"""


class FirefoxNotFoundException(Exception):
    """Raised when Firefox installation cannot be found."""

    pass


class FirefoxCopyException(Exception):
    """Raised when Firefox cannot be copied to temp directory."""

    pass


class FirefoxPatchException(Exception):
    """Raised when Firefox cannot be patched."""

    pass
