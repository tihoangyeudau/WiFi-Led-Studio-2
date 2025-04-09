#!/usr/bin/env python3

from setuptools import setup

import wls.consts as const

PROJECT_DOCS = "https://rainbowmusicled.com"
PROJECT_PACKAGE_NAME = "wls"
PROJECT_VERSION = const.PROJECT_VERSION
PROJECT_LICENSE = "Rainbow Music Led License"
PROJECT_AUTHOR = "Rainbow Music Led"
PROJECT_AUTHOR_EMAIL = "rainbowmusicled@gmail.com"
PROJECT_MAINTAINER = "Rainbow Music Led Developers"
PROJECT_MAINTAINER_EMAIL = "tuantrung2905@gmail.com"
PROJECT_URL = "https://github.com/tihoangyeudau/WiFi-Led-Studio-2"
PROJECT_WEBSITE = "https://rainbowmusicled.com"
PROJECT_DOCS = "https://rainbowmusicled.com"

# Need to install numpy first
SETUP_REQUIRES = [
    "numpy~=1.26.2",
    "wheel>=0.36.2",
]

INSTALL_REQUIRES = [
    "aiohttp~=3.9.1",
    "aiohttp_cors>=0.7.0",
    "aubio>=0.4.9",
    "bokeh>=3.1.0",
    "cython>=3.0.7",
    "certifi>=2023.11.17",
    "multidict>=6.0.4",
    "paho-mqtt>=1.6.1",
    "psutil>=5.9.7",
    "pyserial>=3.5",
    "pystray>=0.19.5",
    "requests>=2.31.0",
    "sacn>=1.9.0",
    "sentry-sdk>=1.40.4",
    "sounddevice>=0.4.6",
    "samplerate>=0.2.1",
    "icmplib>=3.0.4",
    "voluptuous>=0.14.1",
    "zeroconf~=0.119.0",
    "pillow>=10.1.0",
    "stupidartnet~=1.4.0",
    "pyinstaller==6.8.0",
    "cx-freeze>=7.2.2",
    # Conditional Requirement
    # uvloop doesn't work on Windows yet, but should be a good speedup for low power linux devices
    'uvloop>=0.16.0; platform_system != "Windows"',
    # We can install this on all linux devices, it just won't work for anything other than a Pi
]


setup(
    name=PROJECT_PACKAGE_NAME,
    version=PROJECT_VERSION,
    license=PROJECT_LICENSE,
    author=PROJECT_AUTHOR,
    author_email=PROJECT_AUTHOR_EMAIL,
    maintainer=PROJECT_MAINTAINER,
    maintainer_email=PROJECT_MAINTAINER_EMAIL,
    url=PROJECT_URL,
    project_urls={
        "Documentation": PROJECT_DOCS,
        "Website": PROJECT_WEBSITE,
        "Source": PROJECT_URL,
    },
    install_requires=INSTALL_REQUIRES,
    setup_requires=SETUP_REQUIRES,
    python_requires=const.REQUIRED_PYTHON_STRING,
    entry_points={"console_scripts": ["wls = wls.__main__:main"]},
)