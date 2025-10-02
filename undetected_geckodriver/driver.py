import os
import platform
import sys

from loguru import logger as loguru_logger
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.webdriver import WebDriver

from .constants import TO_REPLACE_STRING
from .errors import FirefoxNotFoundException, FirefoxPatchException
from .firefox_manager import FirefoxManager, LockFileWatcher
from .utils import generate_random_string, get_platform_config


class Firefox(WebDriver):
    """
    A custom Firefox WebDriver that attempts to avoid detection by web services.
    """

    def __init__(
        self,
        options: Options | None = None,
        service: Service | None = None,
        lookup_path: str | None = None,
        keep_alive: bool = True,
        debug: bool = False,
    ) -> None:
        """
        Initialize a new undetected Firefox driver.

        Args:
            options: Firefox options
            service: Firefox service
            lookup_path: Path to Firefox installation (uses default if not provided)
            keep_alive: Whether to keep the browser alive after the driver is gone
            debug: Whether to show debug logs (False by default)

        Raises:
            FirefoxNotFoundException: If Firefox is not found
            FirefoxCopyException: If Firefox cannot be copied to temp
            FirefoxPatchException: If Firefox cannot be patched
        """
        # Store debug as an instance attribute to avoid attribute lookup via WebDriverMixin
        # This needs to be set before any other operations that might use self.debug
        self._debug = debug

        # Setup logging based on debug parameter
        self._configure_logging(self._debug)

        # First, perform global cleanup of any orphaned or old Firefox instances
        self._purge_stale_instances(self._debug)

        self.platform_config = get_platform_config()

        # Create the Firefox manager
        self.firefox_manager = FirefoxManager(debug=self._debug)
        self.instance_id = self.firefox_manager.instance_id

        if self._debug:
            loguru_logger.info(f"Creating Firefox instance with ID: {self.instance_id}")

        # Clean up any old Firefox instances and profiles
        self.firefox_manager.cleanup_old_copies()

        # Find Firefox installation
        firefox_paths = self.platform_config.firefox_paths
        self._firefox_path = self.firefox_manager.find_firefox_path(
            custom_path=lookup_path,
            lookup_paths=firefox_paths,
        )

        if self._debug:
            loguru_logger.info(
                f"Instance {self.instance_id}: Using Firefox from: {self._firefox_path}"
            )

        # Copy Firefox to temp dir
        self._undetected_path = self.firefox_manager.create_firefox_copy(
            self._firefox_path
        )
        if self._debug:
            loguru_logger.info(
                f"Instance {self.instance_id}: Undetected path: {self._undetected_path}"
            )

        # Create the profile path
        self._profile_path = self.firefox_manager.create_profile_path()
        if self._debug:
            loguru_logger.info(
                f"Instance {self.instance_id}: Profile path: {self._profile_path}"
            )

        # Patch the Firefox binary
        self._patch_libxul_file()

        # Start the lock file watcher
        self.lock_watcher = LockFileWatcher(
            self.firefox_manager,
            self._undetected_path,
            self._profile_path,
        )
        self.lock_watcher.start()

        # Setup Firefox options and service
        self.service = service or Service()
        self.options = options or Options()
        self.options.binary_location = self._find_platform_dependent_executable()

        # Set custom profile path if available
        if self._profile_path:
            self.options.add_argument("-profile")
            self.options.add_argument(self._profile_path)

        self.keep_alive = keep_alive

        if self._debug:
            loguru_logger.info(
                f"Instance {self.instance_id}: Firefox binary location: {self.options.binary_location}"
            )

        super().__init__(self.options, self.service, self.keep_alive)

    @staticmethod
    def _purge_stale_instances(debug=False):
        """
        Scan temp directories and purge any stale Firefox instances and profiles.
        This is run at startup to ensure cleanup of previously abandoned instances.
        """
        try:
            # Create a temporary manager just for cleanup purposes
            cleanup_manager = FirefoxManager(debug=debug)

            # Perform the actual cleanup
            cleanup_manager.cleanup_old_copies()

            # Also check for and remove any orphaned profiles and firefox copies
            cleanup_manager.deep_clean()

            if debug:
                loguru_logger.info("Completed startup purge of stale Firefox instances")
        except Exception as e:
            if debug:
                loguru_logger.error(f"Error during startup cleanup: {e}")

    def _configure_logging(self, debug):
        """Configure logging based on debug parameter"""
        # Only add the logger if debug is True
        if debug:
            # Remove any existing handlers that match our filter
            # Store handler IDs to remove to avoid modifying dict during iteration
            handlers_to_remove = []
            for handler_id in loguru_logger._core.handlers:
                handlers_to_remove.append(handler_id)

            # Remove all handlers (we'll add back if needed)
            for handler_id in handlers_to_remove:
                try:
                    loguru_logger.remove(handler_id)
                except ValueError:
                    pass  # Handler already removed

            # Add our debug logger
            loguru_logger.add(
                sys.stdout,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{file.path}:{line}</cyan> - <level>{message}</level>",
                colorize=True,
                filter=lambda record: record["name"].startswith(
                    "undetected_geckodriver"
                ),
            )

    def _patch_libxul_file(self) -> None:
        """Patch the libxul file in the undetected Firefox directory."""
        xul = self.platform_config.xul
        libxul_path = os.path.join(self._undetected_path, xul)

        # Handle platform-specific file paths
        if not os.path.exists(libxul_path) and os.name == "nt":
            # On Windows, the file might be in a subdirectory
            for root, dirs, files in os.walk(self._undetected_path):
                if xul in files:
                    libxul_path = os.path.join(root, xul)
                    break

        if not os.path.exists(libxul_path):
            raise FirefoxPatchException(
                f"Could not find {xul} in {self._undetected_path}"
            )

        try:
            # Make sure the file is writable before attempting to modify it
            if not os.access(libxul_path, os.W_OK):
                try:
                    # Try to make the file writable
                    current_mode = os.stat(libxul_path).st_mode
                    os.chmod(libxul_path, current_mode | 0o200)  # Add write permission
                except Exception as e:
                    if self._debug:
                        loguru_logger.error(f"Failed to make {xul} writable: {e}")
                    raise FirefoxPatchException(f"Cannot write to {xul} file: {e}")

            with open(libxul_path, "rb") as file:
                libxul_data = file.read()

            # Check if webdriver string exists in the file before attempting to patch
            if TO_REPLACE_STRING not in libxul_data:
                if self._debug:
                    loguru_logger.warning(
                        f"Could not find '{TO_REPLACE_STRING.decode()}' string in {xul}, skipping patch"
                    )
                return

            random_string = generate_random_string(len(TO_REPLACE_STRING))
            random_bytes = random_string.encode()
            libxul_data = libxul_data.replace(TO_REPLACE_STRING, random_bytes)

            # Write the patched file
            with open(libxul_path, "wb") as file:
                file.write(libxul_data)

            if self._debug:
                loguru_logger.info(f"Successfully patched {xul} file")

        except PermissionError as e:
            raise FirefoxPatchException(
                f"Permission denied when patching {xul} file: {e}"
            )
        except Exception as e:
            raise FirefoxPatchException(f"Failed to patch {xul} file: {e}")

    def _find_platform_dependent_executable(self) -> str:
        """Find the platform-dependent executable for patched Firefox."""
        # Check standard locations first
        for executable in self.platform_config.firefox_execs:
            full_path = os.path.join(self._undetected_path, executable)
            if os.path.exists(full_path) and os.access(full_path, os.X_OK):
                return full_path

        # On macOS, the executable might be in a different location
        if platform.system() == "Darwin":
            # Check for Firefox.app structure
            app_macos = os.path.join(self._undetected_path, "Contents", "MacOS")
            if os.path.exists(app_macos):
                for executable in self.platform_config.firefox_execs:
                    full_path = os.path.join(app_macos, executable)
                    if os.path.exists(full_path) and os.access(full_path, os.X_OK):
                        return full_path

        # If we can't find the executable, search recursively as a last resort
        if self._debug:
            loguru_logger.warning(
                "Could not find Firefox executable in standard locations, searching recursively"
            )

        for root, dirs, files in os.walk(self._undetected_path):
            for file in files:
                if file in self.platform_config.firefox_execs:
                    full_path = os.path.join(root, file)
                    if os.access(full_path, os.X_OK):
                        if self._debug:
                            loguru_logger.info(
                                f"Found Firefox executable at {full_path}"
                            )
                        return full_path

        raise FirefoxNotFoundException(
            f"Could not find any executable in {self._undetected_path}"
        )

    def _get_undetected_geckodriver_path(self) -> str:
        """
        Get the path to the undetected geckodriver directory.
        Used for backward compatibility with tests.

        Returns:
            Path to the undetected geckodriver directory
        """
        return self._undetected_path

    def __del__(self):
        """
        Destructor to ensure cleanup happens even if quit() wasn't called.
        This is a safety net to prevent orphaned temp directories.
        """
        try:
            # Check if quit has already been called
            if hasattr(self, "firefox_manager") and hasattr(self, "_undetected_path"):
                if os.path.exists(self._undetected_path):
                    # Call quit if it hasn't been called yet
                    self.quit()
        except Exception:
            # We're in destructor, can't do much about errors
            pass

    def quit(self):
        """Close the browser and cleanup the temporary files."""
        try:
            # Stop the lock file watcher
            if hasattr(self, "lock_watcher"):
                self.lock_watcher.stop()

            # Quit the browser
            super().quit()
        except Exception as e:
            # Continue with cleanup even if browser quit fails
            if hasattr(self, "_debug") and self._debug:
                loguru_logger.error(f"Error during browser quit: {e}")
        finally:
            # Clean up only this instance's files - not all of them
            try:
                if hasattr(self, "firefox_manager"):
                    self.firefox_manager.cleanup_specific_instance()
            except Exception as e:
                # Log but don't re-raise to allow other cleanup to proceed
                if hasattr(self, "_debug") and self._debug:
                    loguru_logger.error(f"Error during cleanup: {e}")

            # Ensure we've actually quit the Selenium WebDriver
            try:
                if (
                    hasattr(self, "service")
                    and hasattr(self.service, "process")
                    and self.service.process
                ):
                    self.service.stop()
            except Exception:
                pass
