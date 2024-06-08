# Couldn't get this to work. Will revisit.
# from packaging.version import Version

__author__ = "Rainbow Music Led"
__copyright__ = "Rainbow Music Led"
__license__ = "Rainbow Music Led"

PROJECT_NAME = "WiFi Led Studio"

REQUIRED_PYTHON_VERSION = (3, 8, 0)
REQUIRED_PYTHON_STRING = ">={}.{}.{}".format(
    REQUIRED_PYTHON_VERSION[0],
    REQUIRED_PYTHON_VERSION[1],
    REQUIRED_PYTHON_VERSION[2],
)

MAJOR_VERSION = 3
MINOR_VERSION = 2
MICRO_VERSION = 5
POST = 0
DEV = 0
PROJECT_VERSION = "{}.{}.{}".format(
    MAJOR_VERSION, MINOR_VERSION, MICRO_VERSION
)
DEV_VERSION = 0
POST_VERSION = 0
CONFIG_MAJOR_VERSION = 2
CONFIG_MINOR_VERSION = 1
CONFIG_MICRO_VERSION = 0

CONFIGURATION_VERSION = "{}.{}.{}".format(
    CONFIG_MAJOR_VERSION, CONFIG_MINOR_VERSION, CONFIG_MICRO_VERSION
)

if DEV > 0:
    DEV_VERSION = f"{PROJECT_VERSION}-dev{DEV}"
    PROJECT_VERSION = DEV_VERSION

if POST > 0:
    POST_VERSION = f"{PROJECT_VERSION}-post{POST}"
    PROJECT_VERSION = POST_VERSION

__version__ = PROJECT_VERSION

if __name__ == "__main__":
    print(__version__)
