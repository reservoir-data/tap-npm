"""NPM tap class."""

from __future__ import annotations

from singer_sdk import typing as th

from tap_npm._app import TapApp
from tap_npm.client import NPMDownloadsStream, NPMPackageStream

app = TapApp(
    name="tap-npm",
    description="Singer.io tap for extracting data from NPM registry",
    config_jsonschema=th.PropertiesList(
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
            description="Initial date to get downloads from",
        ),
    ),
)

app.add_stream(NPMPackageStream)
app.add_stream(NPMDownloadsStream)
