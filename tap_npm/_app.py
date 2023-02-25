"""Base tap application.

TODO: Consider moving this to singer-sdk.
"""

from __future__ import annotations

import typing as t

from singer_sdk import Stream, Tap
from singer_sdk import typing as th


class TapApp:
    """Tap application."""

    def __init__(  # noqa: PLR0913
        self,
        name: str,
        cls: type[Tap] = Tap,
        description: str | None = None,
        streams: list[Stream] | None = None,
        config_jsonschema: dict[str, t.Any] | th.PropertiesList = None,
    ) -> None:
        """Initialize the application.

        Args:
            name: The tap name.
            cls: The base tap class.
            description: The tap description.
            streams: A list of stream classes.
            config_jsonschema: A JSON schema for the tap configuration.

        Raises:
            ValueError: If config_jsonschema is not a dict or JSONTypeHelper.
        """

        class CustomTap(cls):
            pass

        self.plugin: type[CustomTap] = CustomTap
        self.plugin.name = name
        self.plugin.__doc__ = description or name

        if isinstance(config_jsonschema, dict):
            self.plugin.config_jsonschema = config_jsonschema
        elif isinstance(config_jsonschema, th.JSONTypeHelper):
            self.plugin.config_jsonschema = config_jsonschema.to_dict()
        else:
            errmsg = "config_jsonschema must be a dict or JSONTypeHelper"
            raise TypeError(errmsg)

        self.streams = streams or []

        if "discover_streams" not in self.plugin.__dict__:

            def _discover_streams(tap: CustomTap) -> list[Stream]:
                return [stream_class(tap) for stream_class in self.streams]

            self.plugin.discover_streams = _discover_streams

    def add_stream(self, stream: type[Stream]) -> None:
        """Add a stream to the tap.

        Args:
            stream: The stream class to add.
        """
        self.streams.append(stream)

    def __call__(self) -> None:
        """Run the application."""
        self.plugin.cli()
