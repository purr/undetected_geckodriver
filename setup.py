"""
    Undetected Geckodriver
    ======================
    This package provides a sophisticated wrapper around the
    webdriver.Firefox class from the Selenium package. It
    attempts to avoid detection by web services by patching
    certain parts of the Firefox browser.

    Original author: Bytexenon (https://github.com/Bytexenon)
    Fork maintainer: LunarWatcher (https://github.com/LunarWatcher
"""

import os

from setuptools import setup

DIRNAME = os.path.dirname(__file__)
DESCRIPTION = (
    "A Firefox Selenium WebDriver that patches the browser to avoid detection. "
    "Bypasses services such as Cloudflare, Distil Networks, and more. "
    "Ideal for web scraping, automated testing, and bot development without getting detected."
)
LONG_DESC = open(os.path.join(DIRNAME, "README.md")).read()


# Setup #
setup(
    name="undetected-geckodriver-lw",
    version="2.0.0-rc1",
    packages=["undetected_geckodriver"],
    install_requires=["selenium>=4.10.0", "psutil>=5.8.0"],
    include_package_data=True,
    description=DESCRIPTION,
    long_description=LONG_DESC,
    long_description_content_type="text/markdown",
    author="LunarWatcher",
    author_email="oliviawolfie@pm.me",
    url="https://github.com/LunarWatcher/undetected_geckodriver",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        # "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
    ],
    project_urls={
        "Documentation": "https://github.com/LunarWatcher/undetected_geckodriver#readme",
        "Source": "https://github.com/LunarWatcher/undetected_geckodriver",
        "Tracker": "https://github.com/LunarWatcher/undetected_geckodriver/issues",
        "Changelog": "https://github.com/LunarWatcher/undetected_geckodriver/releases",
    },
    keywords=(
        "selenium firefox webdriver undetected bypass cloudflare distil "
        "web scraping automated testing bot development anti-detection "
        "automation browser automation"
    ),
    python_requires=">=3.6",
    license="MIT",
)
