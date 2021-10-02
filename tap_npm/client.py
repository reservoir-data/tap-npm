"""REST client handling, including NPMStream base class."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote_plus

from singer_sdk.streams import RESTStream

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


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
        # row["timestamps"] = [{"version": k, "timestamp": v} for k, v in times.items()]

        versions: Dict[str, Dict[str, Any]] = row.pop("versions", {})
        versions_list = []
        for ver in versions.values():
            new_ver = {}
            new_ver["_id"] = ver["_id"]
            new_ver["version"] = ver["version"]
            new_ver["homepage"] = ver.get("homepage")
            new_ver["repository"] = ver.get("repository")
            new_ver["scripts"] = ver.get("scripts")
            new_ver["description"] = ver["description"]
            new_ver["dist"] = ver.get("dist")
            new_ver["_npmVersion"] = ver.get("_npmVersion")
            new_ver["_npmUser"] = ver.get("_npmUser")
            new_ver["version_name"] = ver["name"]
            new_ver["version_author"] = ver.get("author") or None
            new_ver["version_maintainers"] = ver.get("maintainers")

            license_type = ver.pop("license")
            new_ver["version_license"] = self._clean_license(license_type)

            versions_list.append(new_ver)
        row["versions"] = versions_list

        dist_tags = row.pop("dist-tags", {})
        row["latest"] = latest = dist_tags.pop("latest", None)
        row["dist_tags"] = list(dist_tags.values())

        users: Dict[str, bool] = row.pop("users", {})
        row["users"] = list(users.keys())

        license_type: Optional[Union[str, dict]] = row.get("license")
        row["license"] = self._clean_license(license_type)

        row["author"] = row.get("author") or None

        return row
