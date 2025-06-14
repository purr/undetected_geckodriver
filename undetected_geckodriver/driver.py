import atexit
import logging
import os
import shutil
import sys
import tempfile
import time
import uuid

import psutil
from loguru import logger as loguru_logger
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.webdriver import WebDriver

from .constants import TO_REPLACE_STRING
from .mixins import WebDriverMixin
from .utils import (
    generate_random_string,
    get_platform_dependent_params,
    get_webdriver_instance,
)

# Configure Loguru with colored output to stdout only
loguru_logger.remove()
loguru_logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{file.path}:{line}</cyan> - <level>{message}</level>",
    colorize=True,
)

logger = logging.getLogger(__name__)

# Global temp directory path
TEMP_FIREFOX_DIR = os.path.join(tempfile.gettempdir(), "undetected_firefox")


# Register cleanup function to run at exit
def cleanup_temp_directory():
    """Clean up the main undetected_firefox directory when the program exits."""
    if os.path.exists(TEMP_FIREFOX_DIR):
        try:
            loguru_logger.info(
                f"Cleaning up main undetected_firefox directory: {TEMP_FIREFOX_DIR}"
            )
            shutil.rmtree(TEMP_FIREFOX_DIR)
        except Exception as e:
            loguru_logger.error(f"Failed to clean up main directory: {e}")


# Register the cleanup function to run at exit
atexit.register(cleanup_temp_directory)


class Firefox(WebDriver, WebDriverMixin):
    """
    A custom Firefox WebDriver that attempts to avoid detection by web services.
    """

    def __init__(
        self,
        options: Options | None = None,
        service: Service | None = None,
        lookup_path: str | None = None,
        custom_firefox_path: str | None = None,
        keep_alive: bool = True,
    ) -> None:
        if lookup_path is not None and not os.path.isdir(lookup_path):
            raise RuntimeError("You passed an override path, but it is not a directory")

        self.lookup_path = lookup_path
        self.custom_firefox_path = custom_firefox_path
        self.instance_id = str(uuid.uuid4())[:8]  # Generate unique ID for this instance

        loguru_logger.info(f"Creating Firefox instance with ID: {self.instance_id}")

        self.webdriver: WebDriver = get_webdriver_instance()
        self._platform_dependent_params: dict = get_platform_dependent_params()
        self._firefox_path: str = self._get_firefox_installation_path()
        self._undetected_path: str = self._get_undetected_firefox_path()

        loguru_logger.info(
            f"Instance {self.instance_id}: Using Firefox from: {self._firefox_path}"
        )
        loguru_logger.info(
            f"Instance {self.instance_id}: Undetected path: {self._undetected_path}"
        )

        self._setup_firefox_environment()

        self.service: Service = service or Service()
        self.options: Options = options or Options()
        self.options.binary_location = self._find_platform_dependent_executable()
        self.keep_alive: bool = keep_alive

        loguru_logger.info(
            f"Instance {self.instance_id}: Firefox binary location: {self.options.binary_location}"
        )

        super().__init__(self.options, self.service, self.keep_alive)

    def _setup_firefox_environment(self):
        """Set up the undetected Firefox environment."""
        self._create_undetected_firefox_directory()
        self._patch_libxul_file()

    def _get_firefox_installation_path(self) -> str:
        """
        Unlike _get_binary_location, this method returns the path to the
        directory containing the Firefox binary and its libraries.
        Normally, it's located in `/usr/lib/firefox`.
        """
        # First check if a custom Firefox path was provided
        if self.custom_firefox_path is not None and os.path.exists(
            self.custom_firefox_path
        ):
            loguru_logger.info(
                f"Instance {self.instance_id}: Using custom Firefox path: {self.custom_firefox_path}"
            )
            return self.custom_firefox_path

        if self.lookup_path is not None and os.path.exists(self.lookup_path):
            loguru_logger.debug(
                f"Instance {self.instance_id}: Path overridden: using {self.lookup_path}"
            )
            return self.lookup_path
        elif self.lookup_path is not None:
            loguru_logger.error(
                f"Instance {self.instance_id}: lookup_path was set, but does not exist. {self.lookup_path} is expected to exist"
            )

        firefox_paths: list = self._platform_dependent_params["firefox_paths"]
        for path in firefox_paths:
            if os.path.exists(path):
                loguru_logger.debug(
                    f"Instance {self.instance_id}: Found FF install in {path}"
                )
                return path

        # Fixes #4
        # If the first method fails, we can try to find the path by running
        # Firefox, checking its process path, and then killing it using psutil.
        # This is a last resort method, and might slow down the initialization.
        for firefox_exec in self._platform_dependent_params["firefox_execs"]:
            if shutil.which(firefox_exec):
                loguru_logger.debug(
                    f"Instance {self.instance_id}: Attempting to locate Firefox via process: {firefox_exec}"
                )
                process = psutil.Popen(
                    [firefox_exec, "--headless", "--new-instance"],
                    stdout=psutil.subprocess.DEVNULL,
                    stderr=psutil.subprocess.DEVNULL,
                )
                time.sleep(0.1)  # Wait for the process to truly start
                process_dir = os.path.dirname(process.exe())
                # Kill the process
                process.kill()
                loguru_logger.info(
                    f"Instance {self.instance_id}: Located Firefox at {process_dir}"
                )
                return process_dir

        raise FileNotFoundError("Could not find Firefox installation path")

    def _get_undetected_firefox_path(self) -> str:
        """Get the path for the undetected Firefox."""
        # Use temp directory with instance ID instead of a fixed location
        temp_dir = os.path.join(TEMP_FIREFOX_DIR, self.instance_id)
        loguru_logger.debug(
            f"Instance {self.instance_id}: Using temp directory: {temp_dir}"
        )
        return temp_dir

    def _create_undetected_firefox_directory(self) -> str:
        """Create a directory for the undetected Firefox if it doesn't exist."""
        if not os.path.exists(self._undetected_path):
            loguru_logger.info(
                f"Instance {self.instance_id}: Creating undetected Firefox directory at {self._undetected_path}"
            )
            os.makedirs(os.path.dirname(self._undetected_path), exist_ok=True)
            shutil.copytree(self._firefox_path, self._undetected_path)
        return self._undetected_path

    def _patch_libxul_file(self) -> None:
        """Patch the libxul file in the undetected Firefox directory."""
        xul: str = self._platform_dependent_params["xul"]
        libxul_path: str = os.path.join(self._undetected_path, xul)
        if not os.path.exists(libxul_path):
            raise FileNotFoundError(f"Could not find {xul}")

        with open(libxul_path, "rb") as file:
            libxul_data = file.read()

        random_string: str = generate_random_string(len(TO_REPLACE_STRING))
        random_bytes: bytes = random_string.encode()
        libxul_data: bytes = libxul_data.replace(TO_REPLACE_STRING, random_bytes)
        loguru_logger.info(f"Instance {self.instance_id}: Patching {xul} file")
        with open(libxul_path, "wb") as file:
            file.write(libxul_data)

    def _find_platform_dependent_executable(self) -> str:
        """Find the platform-dependent executable for patched Firefox."""
        for executable in self._platform_dependent_params["firefox_execs"]:
            full_path: str = os.path.join(self._undetected_path, executable)
            if os.path.exists(full_path):
                return full_path
            loguru_logger.error(
                f"Instance {self.instance_id}: Failed to find FF executable at {full_path}"
            )

        raise FileNotFoundError("Could not find Firefox executable")

    def quit(self):
        """Close the browser and cleanup the temporary files."""
        try:
            super().quit()
        finally:
            # Clean up the instance's temporary directory after quitting
            if os.path.exists(self._undetected_path):
                try:
                    loguru_logger.info(
                        f"Instance {self.instance_id}: Cleaning up instance temporary directory"
                    )
                    shutil.rmtree(self._undetected_path)
                except Exception as e:
                    loguru_logger.error(
                        f"Instance {self.instance_id}: Failed to clean up: {e}"
                    )
