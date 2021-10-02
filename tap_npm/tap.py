"""NPM tap class."""

from typing import List

from singer_sdk import Tap, Stream
from singer_sdk import typing as th
from tap_npm.client import NPMPackageStream

from tap_npm.streams import (
    NPMPackageStream,
)

STREAM_TYPES = [
    NPMPackageStream,
]


class TapNPM(Tap):
    """NPM tap class."""
    name = "tap-npm"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "packages",
            th.ArrayType(th.StringType),
            required=True,
            description="Packages to query from NPM registry"
        ),
    ).to_dict()

    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""
        return [stream_class(tap=self) for stream_class in STREAM_TYPES]
