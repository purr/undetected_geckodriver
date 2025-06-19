"""
Constants and configuration for undetected_geckodriver
"""

import os
from dataclasses import dataclass
from typing import List

# Constants #
TO_REPLACE_STRING = b"webdriver"

# Firefox instance cleanup settings
CLEANUP_THRESHOLD_MINUTES = 20
LOCK_FILE_UPDATE_INTERVAL_SECONDS = 300  # 5 minutes
TEMP_DIR_PREFIX = "ugff_"  # Prefix for temp directories
PROFILE_DIR_PREFIX = "ugff_profile_"  # Prefix for profile directories
PROFILE_FOLDER_NAME = "undetected_geckodriver_profiles"  # Main profile folder name


@dataclass
class PlatformConfig:
    """Configuration for a specific operating system platform"""

    firefox_execs: List[str]
    firefox_paths: List[str]
    xul: str


# Platform-specific configurations
WINDOWS = PlatformConfig(
    firefox_execs=["firefox.exe"],
    firefox_paths=[
        "C:\\Program Files\\Mozilla Firefox",
        "C:\\Program Files (x86)\\Mozilla Firefox",
        os.path.expandvars("%LOCALAPPDATA%\\Mozilla Firefox"),
        os.path.expandvars("%PROGRAMFILES%\\Mozilla Firefox"),
        os.path.expandvars("%PROGRAMFILES(X86)%\\Mozilla Firefox"),
    ],
    xul="xul.dll",
)

MACOS = PlatformConfig(
    firefox_execs=["firefox", "Firefox", "firefox-bin"],
    firefox_paths=[
        "/Applications/Firefox.app/Contents/MacOS",
        "/Applications/Firefox Developer Edition.app/Contents/MacOS",
        "/Applications/Firefox Nightly.app/Contents/MacOS",
        os.path.expanduser("~/Applications/Firefox.app/Contents/MacOS"),
        os.path.expanduser(
            "~/Applications/Firefox Developer Edition.app/Contents/MacOS"
        ),
        os.path.expanduser("~/Applications/Firefox Nightly.app/Contents/MacOS"),
        # Additional Homebrew and MacPorts paths
        "/opt/homebrew/bin",
        "/usr/local/bin",
        "/opt/local/bin",
    ],
    xul="XUL",
)

LINUX = PlatformConfig(
    firefox_execs=["firefox", "firefox-bin", "firefox-esr"],
    firefox_paths=[
        "/usr/lib/firefox",
        "/usr/lib/firefox-esr",
        "/usr/lib/firefox-developer-edition",
        "/usr/lib/firefox-nightly",
        "/usr/lib/firefox-trunk",
        "/usr/lib/firefox-beta",
        "/snap/firefox/current/usr/lib/firefox",
        "/opt/firefox",
        # Additional distro-specific paths
        "/usr/lib64/firefox",
        "/usr/local/firefox",
        "/usr/lib/x86_64-linux-gnu/firefox",
        os.path.expanduser("~/.local/share/flatpak/app/org.mozilla.firefox"),
        "/var/lib/flatpak/app/org.mozilla.firefox",
    ],
    xul="libxul.so",
)

# Map platform names to configs
PLATFORM_CONFIGS = {"Windows": WINDOWS, "Darwin": MACOS, "Linux": LINUX}
