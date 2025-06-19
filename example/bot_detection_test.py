#!/usr/bin/env python3
# Bot detection test - visits multiple anti-bot websites to test undetected capabilities

import json
import time

from selenium.webdriver.common.by import By

import undetected_geckodriver as ug


def main():
    # Create a new undetected Firefox instance
    driver = ug.Firefox()
    results = {}

    try:
        # Test 1: Sannysoft Bot Test
        print("Testing against Sannysoft Bot Detection...")
        driver.get("https://bot.sannysoft.com")
        time.sleep(5)

        # Save screenshot of results
        driver.save_screenshot("sannysoft_results.png")
        results["sannysoft"] = {
            "url": "https://bot.sannysoft.com",
            "screenshot": "sannysoft_results.png",
            "notes": "Check screenshot for detailed test results",
        }

        # Test 2: NowSecure Detection Test
        print("\nTesting against NowSecure Bot Detection...")
        driver.get("https://nowsecure.nl")
        time.sleep(5)

        # Look for the result
        try:
            detected_elements = driver.find_elements(By.CSS_SELECTOR, ".fail")
            not_detected_elements = driver.find_elements(By.CSS_SELECTOR, ".success")

            results["nowsecure"] = {
                "url": "https://nowsecure.nl",
                "detected_count": len(detected_elements),
                "not_detected_count": len(not_detected_elements),
            }

            print(
                f"Detection results - Failed: {len(detected_elements)}, Passed: {len(not_detected_elements)}"
            )
        except Exception as e:
            results["nowsecure"] = {"url": "https://nowsecure.nl", "error": str(e)}

        driver.save_screenshot("nowsecure_results.png")

        # Save all test results to a JSON file
        with open("bot_detection_results.json", "w") as f:
            json.dump(results, f, indent=2)

        print("\nAll tests completed. Results saved to bot_detection_results.json")
        print("Screenshots saved for each test.")

    finally:
        # Clean up
        driver.quit()


if __name__ == "__main__":
    main()
