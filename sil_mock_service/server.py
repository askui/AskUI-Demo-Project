"""
Honda Infotainment SIL Mock Service

A lightweight HTTP server that simulates vehicle subsystem backends for the
Honda infotainment emulator. It serves mock data from the fixtures/ directory
and exposes endpoints to query and mutate state at runtime.

The emulator (or test tooling) can hit these endpoints to:
  - Read current state  (GET)
  - Mutate state        (POST/PATCH)
  - Reset to defaults   (POST /reset)

Usage:
    python -m sil_mock_service.server                       # defaults
    python -m sil_mock_service.server --port 5100           # custom port
    python -m sil_mock_service.server --fixtures ../fixtures # custom path
"""

import argparse
import copy
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

logger = logging.getLogger("sil-mock")

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"

# ── In-memory state (loaded from fixtures, mutable at runtime) ──────────────

_initial_state: dict[str, dict] = {}
_state: dict[str, dict] = {}

DOMAINS = ["bluetooth", "radio", "media", "navigation", "vehicle"]


def load_fixtures(fixtures_dir: Path) -> None:
    """Load all fixture JSON files into the initial state."""
    global _initial_state, _state
    _initial_state = {}
    for domain in DOMAINS:
        fixture_path = fixtures_dir / f"{domain}.json"
        if fixture_path.exists():
            _initial_state[domain] = json.loads(fixture_path.read_text("utf-8"))
            logger.info("Loaded fixture: %s", domain)
        else:
            _initial_state[domain] = {}
            logger.warning("Fixture not found: %s", fixture_path)
    _state = copy.deepcopy(_initial_state)


def reset_state() -> None:
    """Reset all runtime state back to the initial fixture data."""
    global _state
    _state = copy.deepcopy(_initial_state)


def get_domain(domain: str) -> dict | None:
    return _state.get(domain)


def patch_domain(domain: str, patch: dict) -> dict | None:
    """Shallow-merge patch into a domain's state."""
    if domain not in _state:
        return None
    _state[domain].update(patch)
    return _state[domain]


# ── Convenience helpers for common mutations ────────────────────────────────

def bluetooth_connect(device_id: str) -> dict | str:
    """Simulate connecting a Bluetooth device."""
    bt = _state.get("bluetooth", {})
    for device in bt.get("paired_devices", []):
        device["connected"] = False  # disconnect others
    for device in bt.get("paired_devices", []):
        if device["id"] == device_id:
            device["connected"] = True
            return device
    return f"Device {device_id} not found in paired devices"


def bluetooth_disconnect(device_id: str) -> dict | str:
    """Simulate disconnecting a Bluetooth device."""
    bt = _state.get("bluetooth", {})
    for device in bt.get("paired_devices", []):
        if device["id"] == device_id:
            device["connected"] = False
            return device
    return f"Device {device_id} not found in paired devices"


def bluetooth_pair(device_id: str) -> dict | str:
    """Move a device from available to paired."""
    bt = _state.get("bluetooth", {})
    available = bt.get("available_devices", [])
    for i, device in enumerate(available):
        if device["id"] == device_id:
            paired_device = {
                **device,
                "paired": True,
                "connected": False,
                "profiles": ["A2DP"],
                "battery_level": None,
            }
            paired_device.pop("signal_strength", None)
            bt.setdefault("paired_devices", []).append(paired_device)
            available.pop(i)
            return paired_device
    return f"Device {device_id} not found in available devices"


def radio_tune(frequency: float) -> dict:
    """Tune to a specific radio frequency."""
    radio = _state.get("radio", {})
    radio.setdefault("current_state", {})["frequency"] = frequency
    return radio["current_state"]


def media_play(track_id: int | None = None) -> dict:
    """Start playback, optionally jumping to a track."""
    media = _state.get("media", {})
    ps = media.setdefault("playback_state", {})
    if track_id is not None:
        ps["current_track_id"] = track_id
        ps["position_sec"] = 0
    ps["playing"] = True
    return ps


def media_pause() -> dict:
    media = _state.get("media", {})
    ps = media.setdefault("playback_state", {})
    ps["playing"] = False
    return ps


def media_next_track() -> dict:
    media = _state.get("media", {})
    ps = media.setdefault("playback_state", {})
    total = media.get("usb_media", {}).get("total_tracks", 1)
    current = ps.get("current_track_id", 1)
    ps["current_track_id"] = (current % total) + 1
    ps["position_sec"] = 0
    ps["playing"] = True
    return ps


def media_prev_track() -> dict:
    media = _state.get("media", {})
    ps = media.setdefault("playback_state", {})
    total = media.get("usb_media", {}).get("total_tracks", 1)
    current = ps.get("current_track_id", 1)
    ps["current_track_id"] = ((current - 2) % total) + 1
    ps["position_sec"] = 0
    ps["playing"] = True
    return ps


def climate_set_temp(side: str, temp_f: int) -> dict:
    """Set driver or passenger temperature."""
    climate = _state.get("vehicle", {}).get("climate", {})
    key = f"{side}_temp_f"
    if key in climate:
        climate[key] = temp_f
    return climate


def climate_set_fan(speed: int) -> dict:
    climate = _state.get("vehicle", {}).get("climate", {})
    max_speed = climate.get("max_fan_speed", 7)
    climate["fan_speed"] = max(0, min(speed, max_speed))
    return climate


def climate_toggle_ac() -> dict:
    climate = _state.get("vehicle", {}).get("climate", {})
    climate["ac_on"] = not climate.get("ac_on", False)
    return climate


def climate_toggle_auto() -> dict:
    climate = _state.get("vehicle", {}).get("climate", {})
    climate["auto_mode"] = not climate.get("auto_mode", False)
    return climate


def gps_set_position(lat: float, lon: float, speed_kmh: float = 0) -> dict:
    """Update simulated GPS position."""
    nav = _state.get("navigation", {})
    gps = nav.setdefault("gps", {})
    gps["latitude"] = lat
    gps["longitude"] = lon
    gps["speed_kmh"] = speed_kmh
    return gps


# ── HTTP Request Handler ───────────────────────────────────────────────────

class SILHandler(BaseHTTPRequestHandler):
    """Minimal REST-ish handler for the mock service."""

    def _send_json(self, data: dict | list | str, status: int = 200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length))

    # ── GET ────────────────────────────────────────────────────────────────

    def do_GET(self):
        path = self.path.strip("/")

        if path == "" or path == "status":
            self._send_json({
                "service": "Honda SIL Mock Service",
                "domains": DOMAINS,
                "status": "running",
            })
            return

        if path == "state":
            self._send_json(_state)
            return

        # GET /<domain>
        parts = path.split("/")
        domain = parts[0]
        data = get_domain(domain)
        if data is not None:
            self._send_json(data)
        else:
            self._send_json({"error": f"Unknown domain: {domain}"}, 404)

    # ── POST ───────────────────────────────────────────────────────────────

    def do_POST(self):
        path = self.path.strip("/")
        body = self._read_body()

        if path == "reset":
            reset_state()
            self._send_json({"status": "reset", "message": "All state reset to fixtures"})
            return

        # ── Bluetooth actions ──────────────────────────────────────────────
        if path == "bluetooth/connect":
            result = bluetooth_connect(body.get("device_id", ""))
            self._send_json(result if isinstance(result, dict) else {"error": result},
                            200 if isinstance(result, dict) else 404)
            return

        if path == "bluetooth/disconnect":
            result = bluetooth_disconnect(body.get("device_id", ""))
            self._send_json(result if isinstance(result, dict) else {"error": result},
                            200 if isinstance(result, dict) else 404)
            return

        if path == "bluetooth/pair":
            result = bluetooth_pair(body.get("device_id", ""))
            self._send_json(result if isinstance(result, dict) else {"error": result},
                            200 if isinstance(result, dict) else 404)
            return

        # ── Radio actions ──────────────────────────────────────────────────
        if path == "radio/tune":
            self._send_json(radio_tune(body.get("frequency", 87.9)))
            return

        # ── Media actions ──────────────────────────────────────────────────
        if path == "media/play":
            self._send_json(media_play(body.get("track_id")))
            return
        if path == "media/pause":
            self._send_json(media_pause())
            return
        if path == "media/next":
            self._send_json(media_next_track())
            return
        if path == "media/prev":
            self._send_json(media_prev_track())
            return

        # ── Climate actions ────────────────────────────────────────────────
        if path == "climate/temperature":
            self._send_json(climate_set_temp(
                body.get("side", "driver"), body.get("temp_f", 72)))
            return
        if path == "climate/fan":
            self._send_json(climate_set_fan(body.get("speed", 3)))
            return
        if path == "climate/toggle_ac":
            self._send_json(climate_toggle_ac())
            return
        if path == "climate/toggle_auto":
            self._send_json(climate_toggle_auto())
            return

        # ── Navigation actions ─────────────────────────────────────────────
        if path == "navigation/gps":
            self._send_json(gps_set_position(
                body.get("latitude", 0), body.get("longitude", 0),
                body.get("speed_kmh", 0)))
            return

        self._send_json({"error": f"Unknown action: {path}"}, 404)

    # ── PATCH (generic domain update) ──────────────────────────────────────

    def do_PATCH(self):
        path = self.path.strip("/")
        body = self._read_body()
        result = patch_domain(path, body)
        if result is not None:
            self._send_json(result)
        else:
            self._send_json({"error": f"Unknown domain: {path}"}, 404)

    # ── OPTIONS (CORS preflight) ───────────────────────────────────────────

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        logger.info(format, *args)


# ── Entry point ─────────────────────────────────────────────────────────────

def run_server(port: int = 5100, fixtures_dir: Path = FIXTURES_DIR):
    logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")
    load_fixtures(fixtures_dir)
    server = HTTPServer(("127.0.0.1", port), SILHandler)
    logger.info("SIL Mock Service running on http://127.0.0.1:%d", port)
    logger.info("Fixtures loaded from %s", fixtures_dir)
    logger.info("Endpoints: GET /<domain> | POST /<domain>/<action> | POST /reset")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down.")
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Honda SIL Mock Service")
    parser.add_argument("--port", type=int, default=5100)
    parser.add_argument("--fixtures", type=str, default=str(FIXTURES_DIR))
    args = parser.parse_args()
    run_server(port=args.port, fixtures_dir=Path(args.fixtures))
