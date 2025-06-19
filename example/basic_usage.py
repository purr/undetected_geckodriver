#!/usr/bin/env python3
# Basic usage example of undetected_geckodriver

import time

import undetected_geckodriver as ug


def main():
    # Create a new instance of the undetected Firefox driver
    driver = ug.Firefox()

    try:
        # Visit a website that typically detects automation
        driver.get("https://bot.sannysoft.com")

        # Give the page time to load and execute its detection scripts
        time.sleep(5)

        # Take a screenshot of the results
        driver.save_screenshot("basic_usage_result.png")
        print("Screenshot saved as 'basic_usage_result.png'")

        # Optional: Print the page title
        print(f"Page title: {driver.title}")

    finally:
        # Always make sure to quit the driver to clean up resources
        driver.quit()


if __name__ == "__main__":
    main()
