"""NPM tap class."""


from __future__ import annotations

from singer_sdk import Stream, Tap
from singer_sdk import typing as th

from tap_npm.client import NPMDownloadsStream, NPMPackageStream

STREAM_TYPES = [
    NPMPackageStream,
    NPMDownloadsStream,
]


class TapNPM(Tap):
    """NPM tap class."""

    name = "tap-npm"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "packages",
            th.ArrayType(th.StringType),
            required=True,
            description="Packages to query from NPM registry",
        ),
        th.Property(
            "start_date",
            th.DateTimeType,
            default="2015-01-10",
            description="Initial date to get downlaods from",
        ),
    ).to_dict()

    def discover_streams(self) -> list[Stream]:
        """Return a list of discovered streams."""
        return [stream_class(tap=self) for stream_class in STREAM_TYPES]
