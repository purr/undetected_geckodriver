#!/usr/bin/env python3
# Example demonstrating headless mode with undetected_geckodriver

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

import undetected_geckodriver as ug


def main():
    # Create Firefox options
    options = Options()

    # Enable headless mode
    options.headless = True

    print("Creating Firefox driver in headless mode...")
    # Pass options to the Firefox driver
    driver = ug.Firefox(options=options)

    try:
        # Visit a website
        print("Navigating to a test website...")
        driver.get("https://www.python.org")
        time.sleep(3)

        # Get the page title
        title = driver.title
        print(f"Page title: {title}")

        # Find and interact with elements
        search_box = driver.find_element(By.ID, "id-search-field")
        search_box.send_keys("headless firefox")

        # Find the search button and click it
        search_button = driver.find_element(By.ID, "submit")
        search_button.click()
        time.sleep(3)

        # Get search results
        results = driver.find_elements(By.CSS_SELECTOR, ".list-recent-events li")
        print(f"\nFound {len(results)} search results:")

        # Print the first few results
        for i, result in enumerate(results[:5], 1):
            print(
                f"{i}. {result.text[:60]}..."
                if len(result.text) > 60
                else f"{i}. {result.text}"
            )

        # Take a screenshot even in headless mode
        driver.save_screenshot("headless_search_results.png")
        print("\nScreenshot saved as 'headless_search_results.png'")

    finally:
        # Clean up
        driver.quit()
        print("Driver quit successfully")


if __name__ == "__main__":
    main()
