"""Test the tap's core functionality."""

from __future__ import annotations

from singer_sdk.testing import get_tap_test_class

from tap_npm.tap import app

pytest_plugins = ("singer_sdk.testing.pytest_plugin",)


TestTapNPM = get_tap_test_class(
    app.plugin,
    config={
        "packages": ["@evidence-dev/evidence"],
        "start_date": "2021-11-01",
    },
)
