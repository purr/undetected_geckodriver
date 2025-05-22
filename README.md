# Undetected GeckoDriver

Undetected-geckodriver is a patching tool that removes the `webdriver` property directly from the Geckodriver binary

This project is forked from [Bytexenon's project by the same name](https://github.com/bytexenon/undetected_geckodriver) after she archived her version, and is primarily maintained so [the archival efforts of the Stack Exchange data dump](https://github.com/LunarWatcher/se-data-dump-transformer) can continue without Cloudflare outright blocking the archival. 

Undetected geckodriver is not designed to bypass all of Cloudflare on its own; you still need to implement manual captcha stuff on your end if you get hit by a CF captcha wall. This tool exists so those captcha walls, if/when they're hit, aren't forced infinite bot check wall that redirects back to itself. Some sites, like Stack Exchange, have Cloudflare configured so aggressively that running into it is a guarantee; whether that wall can be bypassed with or without human supervision, however, seems to be down to the `navigator.webdriver` attribute.

There are a lot more things that can contribute to hard Cloudflare blocks, but this webdriver at least ensures the webdriver isn't the problem.

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

## Supported operating systems

Only Windows and Linux are supported. macOS is not supported at this time, due to Crapple being crap to work with, it refusing all attempts to debug via Actions, and the only remaining option being to buy hardware for nearly or over 2000 EUR for enough access to debug a relatively basic file-related issue that still requires more hands-on access. 

Pull requests making it work are welcome, and the only way it will be supported.

## Usage

Since Undetected GeckoDriver acts as an interface for Selenium, you can use it the same way you would use Selenium.

You can integrate Undetected GeckoDriver into your existing Selenium code by simply replacing the `selenium.webdriver.Firefox` imports with `undetected_geckodriver.Firefox`.


Initialising the driver is done with:
```python
from undetected_geckodriver import Firefox

driver = Firefox()
```

Everything else is fully compatible with Selenium. For general selenium usage instructions, see [Selenium's own documentation](https://selenium-python.readthedocs.io/)


## Requirements

- Firefox
- Python >= 3.6
- `pip3 install -r requirements.txt`


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 

