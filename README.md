# Undetected GeckoDriver

Undetected-geckodriver is a patching tool that removes the `webdriver` property directly from the Geckodriver binary

This project is forked from [Bytexenon's project by the same name](https://github.com/bytexenon/undetected_geckodriver) after they archived their version, and is primarily maintained so [the archival efforts of the Stack Exchange data dump](https://github.com/LunarWatcher/se-data-dump-transformer) can continue without Cloudflare interfering. 

Undetected geckodriver is not designed to bypass all of Cloudflare on its own; you still need to implement manual captcha stuff on your end if you get hit by a CF captcha wall. This tool exists so those captcha walls, if they're hit, aren't forced infinite bot check wall that redirects back to itself. Some sites, like Stack Exchange, have Cloudflare configured so aggressively that running into it is a guarantee; whether that wall can be bypassed with or without human supervision, however, seems to be down to the `navigator.webdriver` attribute.

## Installation


You can install the package via pip:

```bash
pip install undetected-geckodriver-lw
```

Or you can install it from source:

```bash
git clone https://github.com/LunarWatcher/undetected_geckodriver
cd undetected_geckodriver
pip install .
```

## Usage

Since Undetected GeckoDriver acts as an interface for Selenium, you can use it the same way you would use Selenium.

You can integrate Undetected GeckoDriver into your existing Selenium code by simply replacing the `selenium.webdriver.Firefox` imports with `undetected_geckodriver.Firefox`.

Here are a couple of examples demonstrating how you can use this project:

1. **Creating a new undetected WebDriver instance and navigating to example.com**:

   ```python
   from undetected_geckodriver import Firefox

   driver = Firefox()
   driver.get("https://www.example.com")
   ```

2. **Searching for "Undetected Geckodriver 1337!" on Google**:

   ```python
   import time
   from undetected_geckodriver import Firefox
   from selenium.webdriver.common.by import By

   # Constants
   SEARCH_FOR = "Undetected Geckodriver 1337!"
   GOOGLE_URL = "https://www.google.com"

   # Initialize the undetected Firefox browser
   driver = Firefox()

   # Navigate to Google
   driver.get(GOOGLE_URL)

   # Locate the search box and perform the search
   search_box = driver.find_element(By.NAME, "q")
   search_box.send_keys(SEARCH_FOR)
   search_box.submit()

   # Wait for the page to load
   time.sleep(2)

   # Print the current URL after the search
   print("Current URL:", driver.current_url)

   # Wait for a while to observe the results
   time.sleep(15)

   # Ensure the browser is closed
   driver.quit() # Close the browser
   ```

For further information and advanced usage, you can take a look at the [official Selenium documentation](https://www.selenium.dev/documentation/en/) since Undetected GeckoDriver is built on top of Selenium.

## Requirements

- **`Firefox`**
- **`Python >= 3.6`**
- **`Selenium >= 4.10.0`**
- **`Psutil >= 5.8.0`**

## FAQ

### The browser is still being detected as a bot. What should I do?

If your browser is still being detected as a bot while using Undetected GeckoDriver, it may be due to advanced bot detection mechanisms on the website. In such cases, please open an issue on the GitHub repository with the website URL and any relevant information. This will help in investigating and potentially adding support for it in future releases.

### Why patch the Firefox binary?

When Firefox is controlled remotely by a script (such as when using Selenium), it sets certain properties that can be detected by anti-bot services as defined in the WebDriver specification. Selenium itself doesn't control these properties directly. By patching the Firefox binary, we can prevent it from modifying these properties, allowing us to interact with websites without being detected as a bot.

### Why use Undetected GeckoDriver over undetected-chromedriver?

While undetected-chromedriver is a great tool for bypassing bot detection mechanisms, it only supports Chrome and Edge browsers. Undetected GeckoDriver fills this gap by providing similar functionality for Firefox browsers.


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 

