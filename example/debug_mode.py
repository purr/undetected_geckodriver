#!/usr/bin/env python3
# Example demonstrating debug mode with verbose logging

import time

import undetected_geckodriver as ug


def main():
    # Create driver with debug mode enabled
    # This will show all the verbose logs including Firefox operations
    print("Creating Firefox driver with debug mode enabled...")
    driver = ug.Firefox(debug=True)

    try:
        print("\nNavigating to test website...")
        driver.get("https://nowsecure.nl")  # A site that tests for bot detection
        time.sleep(5)

        # Perform some actions to generate more logs
        print("\nPerforming some actions...")
        if "NowSecure" in driver.title:
            print("Successfully loaded NowSecure test page")

        # Find an element
        try:
            element = driver.find_element("id", "header")
            print(f"Found element with id 'header': {element.text[:50]}...")
        except Exception as e:
            print(f"Could not find element: {e}")

        # Take a screenshot
        driver.save_screenshot("debug_mode_result.png")
        print("Screenshot saved as 'debug_mode_result.png'")

    finally:
        print("\nQuitting driver...")
        # The cleanup process will also be logged verbosely
        driver.quit()


if __name__ == "__main__":
    main()
