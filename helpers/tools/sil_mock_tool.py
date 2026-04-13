"""
AskUI custom tool for interacting with the SIL Mock Service.

Allows the test agent to query and mutate simulated vehicle state
(Bluetooth devices, media, radio, climate, navigation) during test runs.
"""

import json
import urllib.request
import urllib.error
from askui.models.shared.tools import Tool


class SILMockTool(Tool):
    """Query or control the Honda SIL Mock Service during test execution."""

    def __init__(self, base_url: str = "http://127.0.0.1:5100"):
        self._base_url = base_url.rstrip("/")
        super().__init__(
            name="sil_mock_service",
            description=(
                "Interact with the Honda SIL Mock Service to query or change "
                "simulated vehicle state. Use this to set up preconditions "
                "(e.g., connect a Bluetooth device, load a USB track list, "
                "set GPS position) or to verify backend state after a UI action."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "description": "HTTP method",
                        "enum": ["GET", "POST"],
                    },
                    "endpoint": {
                        "type": "string",
                        "description": (
                            "API endpoint path. Examples: "
                            "'bluetooth' (get BT state), "
                            "'bluetooth/connect' (connect a device), "
                            "'bluetooth/pair' (pair a new device), "
                            "'radio' (get radio state), "
                            "'radio/tune' (tune to frequency), "
                            "'media' (get media state), "
                            "'media/play' (start playback), "
                            "'media/pause', 'media/next', 'media/prev', "
                            "'navigation' (get nav/GPS state), "
                            "'navigation/gps' (set GPS position), "
                            "'vehicle' (get full vehicle state), "
                            "'climate/temperature' (set temp), "
                            "'climate/fan' (set fan speed), "
                            "'climate/toggle_ac', 'climate/toggle_auto', "
                            "'reset' (reset all state to fixture defaults), "
                            "'status' (service health check)"
                        ),
                    },
                    "body": {
                        "type": "object",
                        "description": (
                            "JSON body for POST requests. Examples: "
                            "{'device_id': 'bt-001'} for bluetooth/connect, "
                            "{'frequency': 101.3} for radio/tune, "
                            "{'track_id': 3} for media/play, "
                            "{'side': 'driver', 'temp_f': 75} for climate/temperature, "
                            "{'speed': 5} for climate/fan, "
                            "{'latitude': 37.77, 'longitude': -122.42} for navigation/gps"
                        ),
                        "default": {},
                    },
                },
                "required": ["method", "endpoint"],
            },
        )

    def __call__(self, method: str, endpoint: str, body: dict | None = None) -> str:
        url = f"{self._base_url}/{endpoint.strip('/')}"
        body = body or {}

        try:
            if method.upper() == "GET":
                req = urllib.request.Request(url, method="GET")
            else:
                data = json.dumps(body).encode("utf-8")
                req = urllib.request.Request(
                    url, data=data, method=method.upper(),
                    headers={"Content-Type": "application/json"},
                )

            with urllib.request.urlopen(req, timeout=5) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return json.dumps(result, indent=2)

        except urllib.error.URLError as e:
            return (
                f"Error: Could not reach SIL Mock Service at {self._base_url}. "
                f"Make sure it is running (python -m sil_mock_service). "
                f"Detail: {e}"
            )
        except Exception as e:
            return f"Error calling SIL Mock Service: {e}"
