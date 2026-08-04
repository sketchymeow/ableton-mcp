"""Device listing and parameter control."""

from typing import Literal

from ..connection import get_connection

TrackType = Literal["track", "return", "master"]


def register(mcp):
    @mcp.tool()
    def list_devices(track_index: int = 0, track_type: TrackType = "track") -> dict:
        """List a track's devices, including rack chains and drum pads. Each
        device has a LOM path usable with live_get/live_set/live_call for
        anything the curated tools don't cover (e.g. devices nested inside
        racks)."""
        return get_connection().request(
            "get_devices", {"track_index": track_index, "track_type": track_type}
        )

    @mcp.tool()
    def device_parameters(
        track_index: int, device_index: int, track_type: TrackType = "track"
    ) -> dict:
        """List a device's parameters: name, value, range, display string, and
        (for switches/menus) the list of valid options."""
        return get_connection().request(
            "get_device_parameters",
            {"track_index": track_index, "track_type": track_type,
             "device_index": device_index},
        )

    @mcp.tool()
    def set_device_parameter(
        track_index: int,
        device_index: int,
        parameter: int | str,
        value: float | str,
        track_type: TrackType = "track",
    ) -> dict:
        """Set a device parameter by index or name. Pass a number for
        continuous parameters (clamped to the parameter's range) or an option
        name (e.g. "High") for quantized ones. "Device On" with 0/1 turns the
        device off/on."""
        return get_connection().request(
            "set_device_parameter",
            {"track_index": track_index, "track_type": track_type,
             "device_index": device_index, "parameter": parameter, "value": value},
        )

    @mcp.tool()
    def delete_device(
        track_index: int, device_index: int, track_type: TrackType = "track"
    ) -> dict:
        """Remove a device from a track."""
        return get_connection().request(
            "delete_device",
            {"track_index": track_index, "track_type": track_type,
             "device_index": device_index},
        )
