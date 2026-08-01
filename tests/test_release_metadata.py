from release_metadata import (
    APPLICATION_DIRECTORY_NAME,
    PRODUCT_NAME,
    PUBLISHER,
    VERSION,
    display_version,
)


def test_beta_release_metadata_is_centralized_and_displayable() -> None:
    assert PRODUCT_NAME == "Atlas Invoice Studio"
    assert VERSION == "0.9.1-beta"
    assert PUBLISHER == "Atlas"
    assert APPLICATION_DIRECTORY_NAME == "Atlas Invoice Studio"
    assert display_version() == "Atlas Invoice Studio | Version 0.9.1-beta"
