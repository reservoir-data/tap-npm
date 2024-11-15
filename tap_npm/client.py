"""REST client handling, including NPMStream base class."""

from __future__ import annotations

import importlib.resources
import typing as t
from datetime import datetime
from urllib.parse import quote_plus

import requests
from dateutil.relativedelta import relativedelta
from dateutil.tz import UTC
from singer_sdk import typing as th
from singer_sdk.streams import RESTStream, Stream

from tap_npm import schemas

if t.TYPE_CHECKING:
    from collections.abc import Generator

    from singer_sdk.helpers.types import Context

SCHEMAS_DIR = importlib.resources.files(schemas)


def range_pairs(
    start: int, end: int, step: int
) -> Generator[tuple[int, int], None, None]:
    """Yield pairs of numbers from start to end, with step size.

    Args:
        start: The starting number.
        end: The ending number, inclusive.
        step: The step size.

    Yields:
        A tuple of two numbers.
    """
    current_value = start
    for i, n in enumerate(range(start, end, step)):
        if i == 0:
            current_value = n
            continue
        yield current_value, n - 1
        current_value = n
    yield current_value, end - 1


class NPMPackageStream(RESTStream):  # type: ignore[type-arg]
    """NPM Packages stream class."""

    url_base = "https://registry.npmjs.org"
    name = "packages"
    primary_keys: t.ClassVar[list[str]] = ["_id"]
    schema_filepath = SCHEMAS_DIR / "packages.json"
    records_jsonpath = "$"
    path = "/{package}"

    @property
    def partitions(self) -> list[dict[str, t.Any]]:
        """Return a list of partitions.

        Returns:
            A list of partitions.
        """
        return [{"package": quote_plus(package)} for package in self.config["packages"]]

    @staticmethod
    def _clean_license(
        value: str | dict[str, t.Any] | None,
    ) -> dict[str, str | None] | None:
        return {"type": value, "url": None} if isinstance(value, str) else value

    def post_process(
        self,
        row: dict[str, t.Any],
        context: Context | None = None,  # noqa: ARG002
    ) -> dict[str, t.Any]:
        """Post-process a row.

        Args:
            row: The row.
            context: The stream context.

        Returns:
            The processed row.
        """
        times: dict[str, str] = row.pop("time", {})
        row["modified"] = times.pop("modified")
        row["created"] = times.pop("created")
        row["timestamps"] = [{"version": k, "timestamp": v} for k, v in times.items()]

        row.pop("versions", {})

        dist_tags = row.pop("dist-tags", {})
        row["latest"] = dist_tags.pop("latest", None)
        row["dist_tags"] = list(dist_tags.values())

        users: dict[str, bool] = row.pop("users", {})
        row["users"] = list(users.keys())

        license_type: str | dict[str, t.Any] | None = row.get("license")
        row["license"] = self._clean_license(license_type)

        row["author"] = row.get("author") or None

        return row


class NPMDownloadsStream(Stream):
    """NPM downloads stream class."""

    START_DATE = datetime(2016, 1, 1, tzinfo=UTC)
    URL_BASE = "https://api.npmjs.org/downloads/range"

    name = "downloads"
    primary_keys: t.ClassVar[list[str]] = ["package", "day"]
    replication_key = "day"

    schema = th.PropertiesList(
        th.Property("package", th.StringType),
        th.Property("downloads", th.IntegerType),
        th.Property("day", th.DateTimeType),
    ).to_dict()

    @property
    def partitions(self) -> list[dict[str, t.Any]]:
        """Return a list of partitions.

        Returns:
            A list of partitions.
        """
        return [{"package": package} for package in self.config["packages"]]

    def post_process(
        self,
        row: dict[str, t.Any],
        context: Context | None = None,
    ) -> dict[str, t.Any]:
        """Post-process a row.

        Args:
            row: The row.
            context: The stream context.

        Returns:
            The row.
        """
        if context:
            row["package"] = context["package"]
        return row

    def get_records(
        self,
        context: Context | None,
    ) -> Generator[dict[str, t.Any], None, None]:
        """Get download records.

        Args:
            context: The stream context.

        Yields:
            Dictionaries of download records.
        """
        if not context:
            return

        package = context["package"]
        start_date = (self.get_starting_timestamp(context) or self.START_DATE).date()
        now = datetime.now(tz=UTC).date() - relativedelta(days=1)

        for i, j in range_pairs((start_date - now).days, 0, 500):
            start = now + relativedelta(days=i)
            end = now + relativedelta(days=j)

            url = f"{self.URL_BASE}/{start}:{end}/{package}"
            self.logger.info("Requesting downloads from %s", url)

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            for record in data["downloads"]:
                yield {"package": package, **record}
