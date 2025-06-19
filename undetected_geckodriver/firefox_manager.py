"""
Firefox Manager for undetected_geckodriver
"""

import json
import os
import shutil
import tempfile
import time
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from loguru import logger

from .constants import (
    CLEANUP_THRESHOLD_MINUTES,
    LOCK_FILE_UPDATE_INTERVAL_SECONDS,
    PROFILE_DIR_PREFIX,
    PROFILE_FOLDER_NAME,
    TEMP_DIR_PREFIX,
)
from .errors import FirefoxCopyException, FirefoxNotFoundException


class FirefoxManager:
    """Manages Firefox installations, copying, and cleanup."""

    def __init__(self, instance_id=None, debug=False):
        """Initialize the Firefox manager with an optional instance ID"""
        self.instance_id = instance_id or str(uuid.uuid4())[:8]
        self.temp_dir = os.path.join(tempfile.gettempdir(), "undetected_geckodriver")
        self.profiles_dir = os.path.join(tempfile.gettempdir(), PROFILE_FOLDER_NAME)
        self.debug = debug
        self._create_temp_base_dir()
        self._create_profiles_base_dir()

    def _create_temp_base_dir(self):
        """Create the base temp directory if it doesn't exist."""
        if not os.path.exists(self.temp_dir):
            try:
                os.makedirs(self.temp_dir, exist_ok=True)
            except Exception as e:
                if self.debug:
                    logger.error(f"Failed to create temp directory: {e}")

    def _create_profiles_base_dir(self):
        """Create the profiles directory if it doesn't exist."""
        if not os.path.exists(self.profiles_dir):
            try:
                os.makedirs(self.profiles_dir, exist_ok=True)
                if self.debug:
                    logger.info(f"Created profiles directory: {self.profiles_dir}")
            except Exception as e:
                if self.debug:
                    logger.error(f"Failed to create profiles directory: {e}")

    def find_firefox_path(
        self,
        custom_path: Optional[str] = None,
        lookup_paths: Optional[List[str]] = None,
    ) -> str:
        """
        Find Firefox installation path.

        Args:
            custom_path: User-provided Firefox path
            lookup_paths: List of paths to check for Firefox installation

        Returns:
            Path to Firefox installation

        Raises:
            FirefoxNotFoundException: If Firefox cannot be found
        """
        # First check the custom path if provided
        if custom_path and os.path.exists(custom_path):
            if self.debug:
                logger.info(f"Using custom Firefox path: {custom_path}")
            return custom_path

        # Check the lookup paths
        if lookup_paths:
            for path in lookup_paths:
                if path and os.path.exists(path):
                    if self.debug:
                        logger.info(f"Found Firefox installation at: {path}")
                    return path

        # If we get here, Firefox wasn't found
        checked_paths = []
        if custom_path:
            checked_paths.append(custom_path)
        if lookup_paths:
            checked_paths.extend([p for p in lookup_paths if p])

        raise FirefoxNotFoundException(
            f"Firefox not found. Checked paths: {', '.join(checked_paths)}"
        )

    def create_firefox_copy(self, firefox_path: str) -> str:
        """
        Copy Firefox to a temp directory with a unique ID.

        Args:
            firefox_path: Path to the Firefox installation

        Returns:
            Path to the copied Firefox

        Raises:
            FirefoxCopyException: If Firefox cannot be copied
        """
        # Create a unique temp dir with our prefix and ID
        target_dir = os.path.join(self.temp_dir, f"{TEMP_DIR_PREFIX}{self.instance_id}")

        try:
            if os.path.exists(target_dir):
                if self.debug:
                    logger.warning(f"Temp directory already exists: {target_dir}")
                # Don't duplicate if it exists already
                return target_dir

            if self.debug:
                logger.info(f"Copying Firefox from {firefox_path} to {target_dir}")
            shutil.copytree(firefox_path, target_dir)

            # Create the initial lock file
            self.update_lock_file(target_dir)
            return target_dir

        except Exception as e:
            raise FirefoxCopyException(f"Failed to copy Firefox: {e}")

    def create_profile_path(self) -> Optional[str]:
        """
        Create a unique profile path for this Firefox instance.

        Returns:
            Path to the profile directory
        """
        profile_dir = os.path.join(
            self.profiles_dir, f"{PROFILE_DIR_PREFIX}{self.instance_id}"
        )

        try:
            if not os.path.exists(profile_dir):
                os.makedirs(profile_dir, exist_ok=True)
                if self.debug:
                    logger.info(f"Created profile directory: {profile_dir}")
            else:
                if self.debug:
                    logger.info(f"Using existing profile directory: {profile_dir}")

            # Also create a lock file for the profile
            self.update_lock_file(profile_dir)

            return profile_dir
        except Exception as e:
            if self.debug:
                logger.error(f"Failed to create profile directory: {e}")
            # Fall back to default profile creation by Firefox
            return None

    def update_lock_file(self, directory_path: str):
        """
        Update the lock file with the current timestamp.

        Args:
            directory_path: Path to the directory where to create/update the lock
        """
        lock_file = os.path.join(directory_path, "ugff.lock")
        timestamp = datetime.now().timestamp()

        try:
            with open(lock_file, "w") as f:
                json.dump({"timestamp": timestamp, "id": self.instance_id}, f)
        except Exception as e:
            if self.debug:
                logger.error(f"Failed to update lock file: {e}")

    def cleanup_old_copies(self):
        """
        Clean up old Firefox copies and profiles based on their lock file timestamps.
        """
        # Clean up Firefox copies
        self._cleanup_old_directories(self.temp_dir, TEMP_DIR_PREFIX)

        # Clean up profiles
        self._cleanup_old_directories(self.profiles_dir, PROFILE_DIR_PREFIX)

        # Also clean up the default Mozilla profiles for backward compatibility
        self.cleanup_mozilla_profiles()

    def _cleanup_old_directories(self, base_dir: str, prefix: str):
        """
        Helper method to clean up old directories based on lock files.

        Args:
            base_dir: Base directory to check
            prefix: Prefix of directories to check
        """
        if not os.path.exists(base_dir):
            return

        current_time = datetime.now()
        threshold = current_time - timedelta(minutes=CLEANUP_THRESHOLD_MINUTES)

        try:
            for item in os.listdir(base_dir):
                if not item.startswith(prefix):
                    continue

                item_path = os.path.join(base_dir, item)
                lock_file = os.path.join(item_path, "ugff.lock")

                if not os.path.exists(lock_file):
                    if self.debug:
                        logger.warning(f"No lock file found in {item_path}, skipping")
                    continue

                try:
                    with open(lock_file, "r") as f:
                        data = json.load(f)

                    timestamp = data.get("timestamp")
                    if not timestamp:
                        if self.debug:
                            logger.warning(
                                f"Invalid lock file in {item_path}, skipping"
                            )
                        continue

                    last_update = datetime.fromtimestamp(timestamp)

                    if last_update < threshold:
                        if self.debug:
                            logger.info(
                                f"Cleaning up old directory: {item_path} "
                                f"(last updated: {last_update})"
                            )
                        # Clean up directory
                        self.remove_directory(item_path)

                except Exception as e:
                    if self.debug:
                        logger.error(f"Error processing lock file {lock_file}: {e}")

        except Exception as e:
            if self.debug:
                logger.error(f"Error during cleanup of {base_dir}: {e}")

    def remove_directory(self, path: str):
        """
        Delete a directory.

        Args:
            path: Path to the directory
        """
        if not os.path.exists(path):
            return

        try:
            # First, ensure all files in directory are writable to avoid permission errors
            for root, dirs, files in os.walk(path):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        os.chmod(dir_path, 0o755)  # rwx r-x r-x
                    except Exception:
                        pass

                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    try:
                        os.chmod(file_path, 0o644)  # rw- r-- r--
                    except Exception:
                        pass

            # Now try to remove the directory
            shutil.rmtree(path)
            if self.debug:
                logger.info(f"Successfully removed {path}")

        except Exception as e:
            # If standard removal fails, try more aggressive approaches
            if self.debug:
                logger.error(f"Failed to remove {path} with standard method: {e}")

            try:
                # On Windows, use system commands as a fallback
                if os.name == "nt":
                    import subprocess

                    subprocess.run(["rmdir", "/S", "/Q", path], shell=True, check=False)
                    if self.debug and not os.path.exists(path):
                        logger.info(f"Successfully removed {path} using system command")
                else:
                    # On Unix, use rm -rf as a fallback
                    import subprocess

                    subprocess.run(["rm", "-rf", path], check=False)
                    if self.debug and not os.path.exists(path):
                        logger.info(f"Successfully removed {path} using system command")
            except Exception as final_e:
                if self.debug:
                    logger.error(f"All attempts to remove {path} failed: {final_e}")

    def cleanup_specific_instance(self):
        """
        Clean up only the Firefox copy and profile associated with this instance.
        """
        firefox_copy = os.path.join(
            self.temp_dir, f"{TEMP_DIR_PREFIX}{self.instance_id}"
        )
        profile_dir = os.path.join(
            self.profiles_dir, f"{PROFILE_DIR_PREFIX}{self.instance_id}"
        )

        # Also look for temporary Mozilla profiles
        temp_dir = tempfile.gettempdir()
        mozilla_profiles = []

        try:
            # Find and clean any Mozilla profiles that might belong to this instance
            for item in os.listdir(temp_dir):
                if item.startswith("rust_mozprofile"):
                    try:
                        profile_path = os.path.join(temp_dir, item)
                        # Save it for removal after driver processes are definitely dead
                        mozilla_profiles.append(profile_path)
                    except Exception as e:
                        if self.debug:
                            logger.error(f"Error checking Mozilla profile {item}: {e}")
        except Exception as e:
            if self.debug:
                logger.error(f"Error looking for Mozilla profiles: {e}")

        # Remove Firefox copy
        if os.path.exists(firefox_copy):
            if self.debug:
                logger.info(f"Cleaning up Firefox copy: {firefox_copy}")
            self.remove_directory(firefox_copy)

        # Remove profile directory
        if os.path.exists(profile_dir):
            if self.debug:
                logger.info(f"Cleaning up profile directory: {profile_dir}")
            self.remove_directory(profile_dir)

        # Now clean up Mozilla profiles
        for profile_path in mozilla_profiles:
            if self.debug:
                logger.info(f"Cleaning up Mozilla profile: {profile_path}")
            self.remove_directory(profile_path)

        # Force garbage collection to release any file handles
        import gc

        gc.collect()

    def cleanup_mozilla_profiles(self, instance_id=None):
        """
        Clean up Mozilla profiles created by Firefox.

        Args:
            instance_id: Optional instance ID to look for
        """
        temp_dir = tempfile.gettempdir()

        try:
            for item in os.listdir(temp_dir):
                # Handle both rust_mozprofile and the older format
                if item.startswith("rust_mozprofile"):
                    if instance_id is None or instance_id in item:
                        profile_path = os.path.join(temp_dir, item)
                        if self.debug:
                            logger.info(f"Cleaning up Mozilla profile: {profile_path}")
                        try:
                            shutil.rmtree(profile_path)
                        except Exception as e:
                            if self.debug:
                                logger.error(
                                    f"Failed to remove profile {profile_path}: {e}"
                                )
        except Exception as e:
            if self.debug:
                logger.error(f"Failed to cleanup Mozilla profiles: {e}")

    def deep_clean(self):
        """
        Perform a deep cleaning of all undetected_geckodriver related directories.
        This looks for orphaned Firefox copies, profiles and lock files.
        """
        # Check and clean up the main temporary directories
        self._deep_clean_directory(self.temp_dir, TEMP_DIR_PREFIX)
        self._deep_clean_directory(self.profiles_dir, PROFILE_DIR_PREFIX)

        # Check for orphaned Mozilla profiles
        self._cleanup_orphaned_mozilla_profiles()

    def _deep_clean_directory(self, base_dir: str, prefix: str):
        """
        Deeply clean a directory, checking for orphaned or stale files.

        Args:
            base_dir: Base directory to check
            prefix: Prefix of directories to check
        """
        if not os.path.exists(base_dir):
            return

        try:
            # Check each item in the directory
            for item in os.listdir(base_dir):
                if not item.startswith(prefix):
                    continue

                item_path = os.path.join(base_dir, item)
                lock_file = os.path.join(item_path, "ugff.lock")

                # Check for directories without lock files (orphaned)
                if not os.path.exists(lock_file):
                    if self.debug:
                        logger.warning(
                            f"Found orphaned directory without lock file: {item_path}"
                        )
                    self.remove_directory(item_path)
                    continue

                # Check for directories with invalid lock files
                try:
                    with open(lock_file, "r") as f:
                        try:
                            data = json.load(f)

                            # Check if the lock file has a timestamp
                            if "timestamp" not in data:
                                if self.debug:
                                    logger.warning(
                                        f"Invalid lock file in {item_path}, removing directory"
                                    )
                                self.remove_directory(item_path)
                                continue

                        except json.JSONDecodeError:
                            # Invalid JSON in lock file, consider it orphaned
                            if self.debug:
                                logger.warning(
                                    f"Corrupted lock file in {item_path}, removing directory"
                                )
                            self.remove_directory(item_path)
                            continue

                except Exception:
                    # Can't read lock file, treat as orphaned
                    if self.debug:
                        logger.warning(
                            f"Unreadable lock file in {item_path}, removing directory"
                        )
                    self.remove_directory(item_path)

        except Exception as e:
            if self.debug:
                logger.error(f"Error during deep clean of {base_dir}: {e}")

    def _cleanup_orphaned_mozilla_profiles(self):
        """
        Check for and clean up orphaned Mozilla profiles.
        These are profiles that don't have a corresponding Firefox copy.
        """
        temp_dir = tempfile.gettempdir()

        try:
            # Collect all known instance IDs from Firefox copies
            active_ids = set()
            if os.path.exists(self.temp_dir):
                for item in os.listdir(self.temp_dir):
                    if item.startswith(TEMP_DIR_PREFIX):
                        # Extract the instance ID from the directory name
                        instance_id = item[len(TEMP_DIR_PREFIX) :]
                        active_ids.add(instance_id)

            # Check for Mozilla profiles
            for item in os.listdir(temp_dir):
                if item.startswith("rust_mozprofile"):
                    profile_path = os.path.join(temp_dir, item)

                    # Check if this profile belongs to one of our active instances
                    belongs_to_active = False
                    for instance_id in active_ids:
                        if instance_id in item:
                            belongs_to_active = True
                            break

                    # If it doesn't belong to an active instance, clean it up
                    if not belongs_to_active:
                        if self.debug:
                            logger.info(
                                f"Cleaning up orphaned Mozilla profile: {profile_path}"
                            )
                        self.remove_directory(profile_path)

        except Exception as e:
            if self.debug:
                logger.error(f"Error cleaning orphaned Mozilla profiles: {e}")


class LockFileWatcher:
    """Watches and updates the lock file periodically."""

    def __init__(self, firefox_manager, firefox_copy_path, profile_path=None):
        """
        Initialize the lock file watcher.

        Args:
            firefox_manager: FirefoxManager instance
            firefox_copy_path: Path to the copied Firefox
            profile_path: Path to the profile (optional)
        """
        self.firefox_manager = firefox_manager
        self.firefox_copy_path = firefox_copy_path
        self.profile_path = profile_path
        self.running = False
        self.debug = firefox_manager.debug

    def start(self):
        """Start the lock file watcher in a separate thread."""
        import threading

        self.running = True
        self.thread = threading.Thread(
            target=self._update_loop,
            daemon=True,
        )
        self.thread.start()

    def stop(self):
        """Stop the lock file watcher."""
        # Signal the thread to stop
        self.running = False

        # Wait for the thread to terminate
        if hasattr(self, "thread") and self.thread.is_alive():
            try:
                self.thread.join(timeout=2.0)
                if self.debug and self.thread.is_alive():
                    logger.warning(
                        "Lock file watcher thread did not terminate gracefully"
                    )
            except Exception as e:
                if self.debug:
                    logger.error(f"Error while stopping lock file watcher: {e}")

        # Explicitly update lock files one last time before exiting
        # This ensures timestamps are current right before cleanup
        try:
            self.firefox_manager.update_lock_file(self.firefox_copy_path)
            if self.profile_path and os.path.exists(self.profile_path):
                self.firefox_manager.update_lock_file(self.profile_path)
        except Exception as e:
            if self.debug:
                logger.error(f"Error during final lock file update: {e}")

    def _update_loop(self):
        """Update the lock file periodically."""
        while self.running:
            try:
                # Update Firefox copy lock file
                self.firefox_manager.update_lock_file(self.firefox_copy_path)

                # Update profile lock file if it exists
                if self.profile_path and os.path.exists(self.profile_path):
                    self.firefox_manager.update_lock_file(self.profile_path)

            except Exception as e:
                if self.debug:
                    logger.error(f"Error updating lock file: {e}")

            # Sleep for the update interval
            time.sleep(LOCK_FILE_UPDATE_INTERVAL_SECONDS)
