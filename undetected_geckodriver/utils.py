"""
Utility functions for undetected_geckodriver
"""

import os
import platform
import random
import shutil
import string
import subprocess
import time
from typing import Optional

import psutil
from loguru import logger
from selenium import webdriver

from .constants import PLATFORM_CONFIGS, PlatformConfig


def get_webdriver_instance() -> webdriver.Firefox:
    """Create a new blank Firefox webdriver instance."""
    return webdriver.Firefox.__new__(webdriver.Firefox)


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


def find_firefox_process() -> Optional[str]:
    """
    Find a running Firefox process using psutil.

    Returns:
        The Firefox process path or None if not found
    """
    # Get the list of Firefox executable names for the current platform
    platform_config = get_platform_config()
    firefox_execs = platform_config.firefox_execs

    # Add common variations for broader detection
    additional_names = [
        "firefox",
        "firefox.exe",
        "firefoxdeveloperedition",
        "firefoxnightly",
        "firefox-bin",
    ]
    all_execs = set(firefox_execs + additional_names)

    try:
        for proc in psutil.process_iter(["pid", "name", "exe"]):
            try:
                proc_name = proc.info["name"].lower() if proc.info["name"] else ""
                for exec_name in all_execs:
                    if exec_name.lower() in proc_name:
                        # Found Firefox process
                        if proc.info.get("exe"):
                            firefox_dir = os.path.dirname(proc.info["exe"])
                            logger.debug(f"Found Firefox running at: {firefox_dir}")
                            return firefox_dir
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception as e:
        logger.error(f"Error finding Firefox process: {e}")

    return None


def locate_firefox_via_subprocess() -> Optional[str]:
    """
    Attempt to locate Firefox by launching a subprocess.

    Returns:
        The path to Firefox installation directory or None if not found
    """
    platform_config = get_platform_config()
    firefox_execs = platform_config.firefox_execs

    for firefox_exec in firefox_execs:
        # Check if the executable exists in PATH
        firefox_path = shutil.which(firefox_exec)
        if firefox_path:
            try:
                logger.debug(f"Found Firefox in PATH: {firefox_path}")

                # Get the actual installation directory
                firefox_dir = os.path.dirname(firefox_path)

                # On macOS, if we found a symlink, resolve to the actual Firefox.app location
                if platform.system() == "Darwin" and os.path.islink(firefox_path):
                    real_path = os.path.realpath(firefox_path)
                    # If this is inside the .app package, find the .app root
                    if "Firefox.app" in real_path:
                        app_index = real_path.find("Firefox.app")
                        app_path = real_path[: app_index + len("Firefox.app")]
                        firefox_dir = os.path.join(app_path, "Contents/MacOS")
                    else:
                        firefox_dir = os.path.dirname(real_path)

                logger.debug(f"Using Firefox installation directory: {firefox_dir}")
                return firefox_dir

            except Exception as e:
                logger.error(f"Error resolving Firefox path: {e}")

    # If we couldn't find Firefox in PATH, try launching as a subprocess
    for firefox_exec in firefox_execs:
        # Check if the executable exists in PATH - this is redundant but safe
        if shutil.which(firefox_exec):
            try:
                logger.debug(
                    f"Attempting to locate Firefox via process: {firefox_exec}"
                )
                # Start Firefox with headless flag to avoid UI
                process = None
                try:
                    # Use different args for different platforms
                    if platform.system() == "Windows":
                        process = subprocess.Popen(
                            [firefox_exec, "-headless"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            creationflags=subprocess.CREATE_NO_WINDOW,
                        )
                    else:
                        process = subprocess.Popen(
                            [firefox_exec, "--headless", "--no-remote"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )

                    # Wait a bit for process to start
                    time.sleep(1.0)

                    # Try to get process info with psutil
                    proc = psutil.Process(process.pid)
                    process_path = proc.exe()
                    process_dir = os.path.dirname(process_path)

                    # Kill the process before returning
                    process.terminate()
                    try:
                        process.wait(timeout=1)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=1)

                    logger.info(f"Located Firefox at {process_dir}")
                    return process_dir

                finally:
                    # Make sure the process is terminated
                    if process and process.poll() is None:
                        try:
                            process.kill()
                        except Exception:
                            pass

            except Exception as e:
                logger.error(f"Failed to locate Firefox via subprocess: {e}")

    # Final fallback for macOS - check standard app locations even if not in PATH
    if platform.system() == "Darwin":
        mac_paths = [
            "/Applications/Firefox.app/Contents/MacOS",
            os.path.expanduser("~/Applications/Firefox.app/Contents/MacOS"),
        ]
        for path in mac_paths:
            if os.path.exists(path):
                logger.info(f"Found Firefox in standard macOS location: {path}")
                return path

    return None
