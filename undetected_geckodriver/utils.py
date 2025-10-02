"""
Utility functions for undetected_geckodriver
"""

import platform
import random
import string

from .constants import PLATFORM_CONFIGS, PlatformConfig


def get_platform_config() -> PlatformConfig:
    """Get platform configuration for the current OS."""
    system = platform.system()
    if system not in PLATFORM_CONFIGS:
        raise OSError(f"Unsupported system: {system}")

    return PLATFORM_CONFIGS[system]


def generate_random_string(length: int) -> str:
    """Generate a random alphanumeric string of the specified length."""
    return "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(length)
    )
