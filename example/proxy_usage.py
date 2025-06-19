#!/usr/bin/env python3
# Example demonstrating proxy usage with undetected_geckodriver

import time

from selenium.webdriver.firefox.options import Options

import undetected_geckodriver as ug


def main():
    # Create Firefox options
    options = Options()

    # Configure proxy
    # IMPORTANT: Replace with your actual proxy details
    PROXY_HOST = "127.0.0.1"  # Example proxy address
    PROXY_PORT = "8080"  # Example proxy port

    # Set proxy settings in Firefox options
    options.set_preference("network.proxy.type", 1)  # Manual proxy configuration
    options.set_preference("network.proxy.http", PROXY_HOST)
    options.set_preference("network.proxy.http_port", int(PROXY_PORT))
    options.set_preference("network.proxy.ssl", PROXY_HOST)  # Use same proxy for HTTPS
    options.set_preference("network.proxy.ssl_port", int(PROXY_PORT))

    # Optional: Set proxy for FTP and SOCKS if needed
    # options.set_preference("network.proxy.ftp", PROXY_HOST)
    # options.set_preference("network.proxy.ftp_port", int(PROXY_PORT))
    # options.set_preference("network.proxy.socks", PROXY_HOST)
    # options.set_preference("network.proxy.socks_port", int(PROXY_PORT))

    # Optional: Set no proxy for certain addresses
    # options.set_preference("network.proxy.no_proxies_on", "localhost,127.0.0.1")

    print("Creating Firefox driver with proxy configuration...")
    driver = ug.Firefox(options=options)

    try:
        # For testing proxy, we'll visit a site that shows your IP address
        print("Navigating to site to check IP address (through proxy)...")
        driver.get("https://api.ipify.org")
        time.sleep(3)

        # Get the page source which should contain the IP
        ip_address = driver.page_source
        print(f"Current IP address (should be your proxy's IP): {ip_address}")

        # Visit another site to test the proxy
        print("\nVisiting another site through proxy...")
        driver.get("https://www.whatismyip.com/")
        time.sleep(5)

        # Take screenshot of the results
        driver.save_screenshot("proxy_test_result.png")
        print("Screenshot saved as 'proxy_test_result.png'")

    finally:
        # Clean up
        driver.quit()
        print("Driver quit successfully")

    print(
        "\nNOTE: If you didn't configure a real working proxy, this example might not"
    )
    print("have worked correctly. Check that your proxy settings are valid.")


if __name__ == "__main__":
    main()
