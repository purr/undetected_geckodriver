#!/usr/bin/env python3
# Example demonstrating advanced options and customizations

import os
import tempfile
import time

from selenium.webdriver.firefox.options import Options

import undetected_geckodriver as ug


def main():
    # Create a custom Firefox profile directory
    # This allows for persistent profiles across sessions
    profile_path = os.path.join(tempfile.gettempdir(), "undetected_profile")
    os.makedirs(profile_path, exist_ok=True)
    print(f"Using custom profile at: {profile_path}")

    # Create Firefox options with advanced settings
    options = Options()

    # Set various preferences
    # Disable various features for privacy and performance
    options.set_preference(
        "dom.webnotifications.enabled", False
    )  # Disable notifications
    options.set_preference("media.volume_scale", "0.0")  # Mute audio
    options.set_preference(
        "browser.privatebrowsing.autostart", True
    )  # Private browsing
    options.set_preference("browser.cache.disk.enable", False)  # Disable disk cache

    # Set download behavior
    download_dir = os.path.join(os.getcwd(), "downloads")
    os.makedirs(download_dir, exist_ok=True)
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.manager.showWhenStarting", False)
    options.set_preference("browser.download.dir", download_dir)
    options.set_preference(
        "browser.helperApps.neverAsk.saveToDisk",
        "application/pdf,application/x-pdf,application/octet-stream",
    )

    # Additional arguments
    options.add_argument("--width=1920")
    options.add_argument("--height=1080")

    # Create the Firefox driver with our advanced configuration
    print("Creating Firefox driver with advanced options...")
    driver = ug.Firefox(
        options=options, profile_path=profile_path, headless=False, debug=True
    )

    try:
        # Test the browser configuration
        print("\nTesting download settings...")
        # Visit a site with downloadable content
        driver.get("https://www.mozilla.org/en-US/firefox/new/")
        time.sleep(3)

        # Display user agent
        user_agent = driver.execute_script("return navigator.userAgent")
        print(f"\nCurrent User-Agent: {user_agent}")

        # Check if browser is in private mode
        try:
            is_private = driver.execute_script(
                "return window.navigator.mozPrivateBrowsing?.enabled || "
                + "('incognito' in window.chrome && window.chrome.incognito)"
            )
            print(f"Private browsing mode: {is_private}")
        except Exception:
            print("Could not determine private browsing status")

        # Check window size
        window_size = driver.execute_script(
            "return [window.outerWidth, window.outerHeight]"
        )
        print(f"Window size: {window_size[0]}x{window_size[1]}")

        # Take screenshot of the configured browser
        driver.save_screenshot("advanced_config_result.png")
        print("\nScreenshot saved as 'advanced_config_result.png'")

        # Show cookie settings
        print("\nCookies after visiting site:")
        cookies = driver.get_cookies()
        for i, cookie in enumerate(cookies[:5], 1):  # Show first 5 cookies
            print(
                f"{i}. {cookie['name']}: {cookie['value'][:30]}..."
                if len(cookie["value"]) > 30
                else f"{i}. {cookie['name']}: {cookie['value']}"
            )

        if len(cookies) > 5:
            print(f"...and {len(cookies) - 5} more cookies")

    finally:
        # Clean up
        driver.quit()
        print("\nDriver quit successfully")
        print(f"Profile data saved at: {profile_path}")
        print(f"Downloads directory: {download_dir}")


if __name__ == "__main__":
    main()
