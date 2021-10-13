"""REST client handling, including NPMStream base class."""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
from urllib.parse import quote_plus

from dateutil.relativedelta import relativedelta
from dateutil.tz import UTC

import requests

from singer_sdk import typing as th
from singer_sdk.streams import RESTStream, Stream

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")

def range_pairs(start: int, end: int, step: int):
    current_value = start
    for i, n in enumerate(range(start, end, step)):
        if i == 0:
            continue
        yield current_value, n - 1
        current_value = n
    yield current_value, end


class NPMPackageStream(RESTStream):
    """NPM Packages stream class."""

    url_base = "https://registry.npmjs.org"
    name = "packages"
    primary_keys = ["_id"]
    schema_filepath = SCHEMAS_DIR / "packages.json"
    records_jsonpath = "$"
    path = "/{package}"

    @property
    def partitions(self) -> List[dict]:
        return [{"package": quote_plus(package)} for package in self.config["packages"]]

    @staticmethod
    def _clean_license(value: Optional[Union[str, dict]]) -> Dict[str, Optional[str]]:
        if isinstance(value, str):
            value = {"type": value, "url": None}
        return value

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        times: Dict[str, str] = row.pop("time", {})
        row["modified"] = times.pop("modified")
        row["created"] = times.pop("created")
        row["timestamps"] = [{"version": k, "timestamp": v} for k, v in times.items()]

        row.pop("versions", {})

        dist_tags = row.pop("dist-tags", {})
        row["latest"] = latest = dist_tags.pop("latest", None)
        row["dist_tags"] = list(dist_tags.values())

        users: Dict[str, bool] = row.pop("users", {})
        row["users"] = list(users.keys())

        license_type: Optional[Union[str, dict]] = row.get("license")
        row["license"] = self._clean_license(license_type)

        row["author"] = row.get("author") or None

        return row


class NPMDownloadsStream(Stream):
    """NPM downloads stream class."""

    START_DATE = datetime(2016, 1, 1)
    URL_BASE = "https://api.npmjs.org/downloads/range"

    name = "downloads"
    primary_keys = ["package", "day"]
    replication_key = "day"

    schema = th.PropertiesList(
        th.Property("package", th.StringType),
        th.Property("downloads", th.IntegerType),
        th.Property("day", th.DateTimeType),
    ).to_dict()

    @property
    def partitions(self) -> List[dict]:
        return [{"package": package} for package in self.config["packages"]]

    def post_process(self, row: dict, context: Optional[dict] = None) -> dict:
        row["package"] = context["package"]
        return row

    def get_records(self, context: dict):
        package = context["package"]
        start_date = (self.get_starting_timestamp(context) or self.START_DATE).date()
        now = datetime.now(tz=UTC).date() - relativedelta(days=1)

        for i, j in range_pairs((start_date - now).days, 0, 500):
            start = now + relativedelta(days=i)
            end = now + relativedelta(days=j)

            url = f"{self.URL_BASE}/{start}:{end}/{package}"
            self.logger.info("Requesting downloads from %s", url)

            response = requests.get(url)
            response.raise_for_status()

            data = response.json()

            for record in data["downloads"]:
                yield {"package": package, **record}
