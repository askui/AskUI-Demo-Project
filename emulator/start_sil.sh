#!/usr/bin/env bash
#
# start_sil.sh — Launch the Honda infotainment SIL environment
#
# Starts the SIL mock service, boots the Android Automotive emulator,
# sets up ADB port forwarding, and waits for everything to be ready.
#
# Usage:
#   ./emulator/start_sil.sh                    # defaults
#   ./emulator/start_sil.sh --avd MyHondaAVD   # custom AVD name
#   ./emulator/start_sil.sh --skip-emulator     # mock service only (emulator already running)
#
set -euo pipefail

# ── Configuration ───────────────────────────────────────────────────────────

AVD_NAME="${AVD_NAME:-Honda_Infotainment}"
MOCK_PORT="${MOCK_PORT:-5100}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SKIP_EMULATOR=false

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --avd)       AVD_NAME="$2"; shift 2 ;;
        --port)      MOCK_PORT="$2"; shift 2 ;;
        --skip-emulator) SKIP_EMULATOR=true; shift ;;
        -h|--help)
            echo "Usage: $0 [--avd AVD_NAME] [--port MOCK_PORT] [--skip-emulator]"
            exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ── Locate tools ────────────────────────────────────────────────────────────

# Find Android SDK (common macOS locations)
if [[ -z "${ANDROID_HOME:-}" ]]; then
    for candidate in "$HOME/Library/Android/sdk" "$HOME/Android/Sdk" "/usr/local/share/android-sdk"; do
        if [[ -d "$candidate" ]]; then
            export ANDROID_HOME="$candidate"
            break
        fi
    done
fi

if [[ -z "${ANDROID_HOME:-}" ]]; then
    echo "ERROR: ANDROID_HOME not set and Android SDK not found."
    echo "       Set ANDROID_HOME or install Android Studio."
    exit 1
fi

EMULATOR="$ANDROID_HOME/emulator/emulator"
ADB="$ANDROID_HOME/platform-tools/adb"

# Verify tools exist
for tool in "$EMULATOR" "$ADB"; do
    if [[ ! -x "$tool" ]]; then
        echo "ERROR: $tool not found. Install via Android Studio SDK Manager."
        exit 1
    fi
done

echo "Android SDK: $ANDROID_HOME"
echo "AVD:         $AVD_NAME"
echo "Mock port:   $MOCK_PORT"
echo ""

# ── Step 1: Start SIL Mock Service ─────────────────────────────────────────

echo "▸ Starting SIL Mock Service on port $MOCK_PORT..."
python -m sil_mock_service --port "$MOCK_PORT" &
MOCK_PID=$!

# Wait for it to be ready
for i in $(seq 1 10); do
    if curl -s "http://127.0.0.1:$MOCK_PORT/status" > /dev/null 2>&1; then
        echo "  Mock service ready (PID $MOCK_PID)"
        break
    fi
    if [[ $i -eq 10 ]]; then
        echo "ERROR: Mock service failed to start"
        kill $MOCK_PID 2>/dev/null
        exit 1
    fi
    sleep 1
done

# ── Step 2: Launch Android Emulator ────────────────────────────────────────

if [[ "$SKIP_EMULATOR" == "false" ]]; then
    # Check AVD exists
    if ! "$EMULATOR" -list-avds 2>/dev/null | grep -q "^${AVD_NAME}$"; then
        echo ""
        echo "ERROR: AVD '$AVD_NAME' not found."
        echo ""
        echo "Available AVDs:"
        "$EMULATOR" -list-avds 2>/dev/null || true
        echo ""
        echo "Create one with:  $SCRIPT_DIR/create_avd.sh"
        echo "Or specify:       $0 --avd <name>"
        kill $MOCK_PID 2>/dev/null
        exit 1
    fi

    echo ""
    echo "▸ Launching Android Emulator (AVD: $AVD_NAME)..."
    "$EMULATOR" -avd "$AVD_NAME" -no-snapshot-load -gpu auto &
    EMU_PID=$!

    # Wait for the emulator to boot
    echo "  Waiting for emulator to boot..."
    "$ADB" wait-for-device
    # Wait for boot_completed property
    for i in $(seq 1 120); do
        BOOT=$("$ADB" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')
        if [[ "$BOOT" == "1" ]]; then
            echo "  Emulator booted (PID $EMU_PID)"
            break
        fi
        if [[ $i -eq 120 ]]; then
            echo "ERROR: Emulator failed to boot within 120 seconds"
            kill $MOCK_PID $EMU_PID 2>/dev/null
            exit 1
        fi
        sleep 1
    done
else
    echo ""
    echo "▸ Skipping emulator launch (--skip-emulator)"
    # Verify an emulator is already connected
    if ! "$ADB" devices | grep -q "emulator"; then
        echo "WARNING: No emulator detected via ADB. Is it running?"
    fi
fi

# ── Step 3: ADB Port Forwarding ────────────────────────────────────────────

echo ""
echo "▸ Setting up ADB port forwarding..."

# adb reverse: makes host port accessible from inside the emulator at localhost
"$ADB" reverse tcp:"$MOCK_PORT" tcp:"$MOCK_PORT"
echo "  adb reverse tcp:$MOCK_PORT tcp:$MOCK_PORT  ✓"
echo "  Emulator can reach mock service at http://127.0.0.1:$MOCK_PORT"
echo "  (also available at http://10.0.2.2:$MOCK_PORT)"

# ── Step 4: Verify connectivity from emulator ──────────────────────────────

echo ""
echo "▸ Verifying mock service is reachable from emulator..."
RESPONSE=$("$ADB" shell "curl -s http://127.0.0.1:$MOCK_PORT/status" 2>/dev/null || true)
if echo "$RESPONSE" | grep -q "running"; then
    echo "  Emulator → Mock Service: connected ✓"
else
    echo "  WARNING: Could not verify connectivity from emulator."
    echo "  The emulator app should use http://10.0.2.2:$MOCK_PORT as fallback."
fi

# ── Ready ───────────────────────────────────────────────────────────────────

echo ""
echo "════════════════════════════════════════════════════════"
echo "  SIL Environment Ready"
echo "════════════════════════════════════════════════════════"
echo "  Mock service:  http://127.0.0.1:$MOCK_PORT  (PID $MOCK_PID)"
echo "  Emulator AVD:  $AVD_NAME"
echo "  ADB reverse:   tcp:$MOCK_PORT → tcp:$MOCK_PORT"
echo ""
echo "  Run tests with:"
echo "    python main.py tests/infotainment"
echo ""
echo "  Press Ctrl+C to shut down the SIL environment."
echo "════════════════════════════════════════════════════════"

# ── Trap cleanup ────────────────────────────────────────────────────────────

cleanup() {
    echo ""
    echo "Shutting down SIL environment..."
    "$ADB" reverse --remove-all 2>/dev/null || true
    kill $MOCK_PID 2>/dev/null || true
    echo "Done."
}
trap cleanup EXIT INT TERM

# Keep script alive (mock service runs in background)
wait $MOCK_PID
