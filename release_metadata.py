"""Single source of truth for beta release identity."""

PRODUCT_NAME = "Atlas Invoice Studio"
VERSION = "0.9.0-beta"
PUBLISHER = "Atlas"
APPLICATION_DIRECTORY_NAME = "Atlas Invoice Studio"


def display_version() -> str:
    return f"{PRODUCT_NAME}  •  Version {VERSION}"
