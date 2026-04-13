#!/usr/bin/env bash
#
# create_avd.sh — Create an Android Automotive AVD for Honda infotainment SIL testing
#
# Downloads the required system image and creates an AVD configured for
# automotive infotainment emulation.
#
# Usage:
#   ./emulator/create_avd.sh                            # defaults
#   ./emulator/create_avd.sh --name MyHonda --api 34    # custom
#
set -euo pipefail

# ── Configuration ───────────────────────────────────────────────────────────

AVD_NAME="${AVD_NAME:-Honda_Infotainment}"
API_LEVEL="${API_LEVEL:-34}"
DEVICE_PROFILE="automotive_1024p_landscape"

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --name) AVD_NAME="$2"; shift 2 ;;
        --api)  API_LEVEL="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: $0 [--name AVD_NAME] [--api API_LEVEL]"
            echo ""
            echo "  --name   AVD name (default: Honda_Infotainment)"
            echo "  --api    Android API level (default: 34)"
            echo ""
            echo "Prerequisites: Android Studio with SDK Manager"
            exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ── Locate SDK tools ───────────────────────────────────────────────────────

if [[ -z "${ANDROID_HOME:-}" ]]; then
    for candidate in "$HOME/Library/Android/sdk" "$HOME/Android/Sdk"; do
        if [[ -d "$candidate" ]]; then
            export ANDROID_HOME="$candidate"
            break
        fi
    done
fi

if [[ -z "${ANDROID_HOME:-}" ]]; then
    echo "ERROR: ANDROID_HOME not set. Install Android Studio first."
    exit 1
fi

SDKMANAGER="$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager"
AVDMANAGER="$ANDROID_HOME/cmdline-tools/latest/bin/avdmanager"

# Fallback to older tool paths
if [[ ! -x "$SDKMANAGER" ]]; then
    SDKMANAGER="$ANDROID_HOME/tools/bin/sdkmanager"
fi
if [[ ! -x "$AVDMANAGER" ]]; then
    AVDMANAGER="$ANDROID_HOME/tools/bin/avdmanager"
fi

for tool in "$SDKMANAGER" "$AVDMANAGER"; do
    if [[ ! -x "$tool" ]]; then
        echo "ERROR: $tool not found."
        echo "       Install 'Android SDK Command-line Tools' via Android Studio SDK Manager."
        exit 1
    fi
done

# ── System image selection ──────────────────────────────────────────────────

# Android Automotive system images (prefer x86_64 for Mac performance)
# On Apple Silicon Macs, use arm64-v8a
ARCH="x86_64"
if [[ "$(uname -m)" == "arm64" ]]; then
    ARCH="arm64-v8a"
fi

SYSTEM_IMAGE="system-images;android-${API_LEVEL};android-automotive;${ARCH}"
SYSTEM_IMAGE_ALT="system-images;android-${API_LEVEL};android-automotive-playstore;${ARCH}"

echo "Android SDK:    $ANDROID_HOME"
echo "AVD Name:       $AVD_NAME"
echo "API Level:      $API_LEVEL"
echo "Architecture:   $ARCH"
echo "System Image:   $SYSTEM_IMAGE"
echo ""

# ── Step 1: Accept licenses ────────────────────────────────────────────────

echo "▸ Accepting SDK licenses..."
yes 2>/dev/null | "$SDKMANAGER" --licenses > /dev/null 2>&1 || true

# ── Step 2: Download system image ──────────────────────────────────────────

echo "▸ Downloading Android Automotive system image..."
if "$SDKMANAGER" --install "$SYSTEM_IMAGE" 2>/dev/null; then
    CHOSEN_IMAGE="$SYSTEM_IMAGE"
elif "$SDKMANAGER" --install "$SYSTEM_IMAGE_ALT" 2>/dev/null; then
    CHOSEN_IMAGE="$SYSTEM_IMAGE_ALT"
    echo "  Using Play Store variant: $SYSTEM_IMAGE_ALT"
else
    echo ""
    echo "ERROR: Could not download an Android Automotive image for API $API_LEVEL ($ARCH)."
    echo ""
    echo "Available automotive images:"
    "$SDKMANAGER" --list 2>/dev/null | grep "android-automotive" || echo "  (none found)"
    echo ""
    echo "Options:"
    echo "  1. Open Android Studio → SDK Manager → SDK Platforms → check 'Android Automotive' images"
    echo "  2. Try a different API level:  $0 --api 33"
    echo "  3. On Apple Silicon, ensure arm64-v8a images are available"
    exit 1
fi

echo "  System image ready: $CHOSEN_IMAGE"

# ── Step 3: Create AVD ─────────────────────────────────────────────────────

echo ""
echo "▸ Creating AVD: $AVD_NAME..."

# Delete existing AVD with same name
"$AVDMANAGER" delete avd --name "$AVD_NAME" 2>/dev/null || true

echo "no" | "$AVDMANAGER" create avd \
    --name "$AVD_NAME" \
    --package "$CHOSEN_IMAGE" \
    --device "$DEVICE_PROFILE" \
    --force

echo "  AVD created: $AVD_NAME"

# ── Step 4: Configure AVD for infotainment ──────────────────────────────────

AVD_DIR="$HOME/.android/avd/${AVD_NAME}.avd"
CONFIG_FILE="$AVD_DIR/config.ini"

if [[ -f "$CONFIG_FILE" ]]; then
    echo ""
    echo "▸ Configuring AVD hardware..."

    # Set landscape orientation and automotive-friendly resolution
    cat >> "$CONFIG_FILE" <<CONF

# Honda Infotainment SIL Configuration
hw.lcd.width=1920
hw.lcd.height=1080
hw.lcd.density=160
hw.keyboard=yes
hw.gpu.enabled=yes
hw.gpu.mode=auto
hw.ramSize=4096
hw.initialOrientation=landscape
disk.dataPartition.size=4096M
CONF

    echo "  Display: 1920x1080 landscape"
    echo "  RAM: 4096 MB"
    echo "  GPU: auto (hardware acceleration)"
fi

# ── Done ────────────────────────────────────────────────────────────────────

echo ""
echo "════════════════════════════════════════════════════════"
echo "  AVD '$AVD_NAME' is ready"
echo "════════════════════════════════════════════════════════"
echo ""
echo "  Launch it with:"
echo "    ./emulator/start_sil.sh"
echo ""
echo "  Or manually:"
echo "    $ANDROID_HOME/emulator/emulator -avd $AVD_NAME"
echo ""
echo "  To customize further, open Android Studio → Device Manager"
echo "════════════════════════════════════════════════════════"
