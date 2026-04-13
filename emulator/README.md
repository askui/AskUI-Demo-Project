# Honda Infotainment SIL Emulator Setup

Guide for setting up the Android Automotive emulator in Android Studio for Honda infotainment SIL testing on macOS.

## Prerequisites

- **Android Studio** (Hedgehog or newer recommended)
- **Android SDK** with:
  - Android Automotive system image (API 34 recommended)
  - Android SDK Platform-Tools (for ADB)
  - Android Emulator
- **Python 3.12+** (for the SIL mock service)

## Quick Start

```bash
# 1. Create the Android Automotive AVD (one-time)
./emulator/create_avd.sh

# 2. Start everything (mock service + emulator + port forwarding)
./emulator/start_sil.sh

# 3. In another terminal, run the tests
python main.py tests/infotainment
```

## Manual Setup via Android Studio

If you prefer to set up the AVD through the Android Studio GUI:

### Step 1: Install the Automotive System Image

1. Open Android Studio → **Settings** → **Languages & Frameworks** → **Android SDK**
2. Go to the **SDK Platforms** tab
3. Check **Show Package Details** (bottom right)
4. Under **Android 14.0 (API 34)**, check:
   - `Android Automotive with Google APIs ARM 64 v8a System Image` (Apple Silicon)
   - `Android Automotive with Google APIs Intel x86_64 Atom System Image` (Intel Mac)
5. Click **Apply** to download

### Step 2: Create the AVD

1. Open **Device Manager** (toolbar icon or **Tools → Device Manager**)
2. Click **Create Virtual Device**
3. In the **Category** sidebar, select **Automotive**
4. Choose a device profile:
   - `Automotive (1024p landscape)` — 1920×1080, good for infotainment
   - `Automotive (1080p landscape)` — 1920×1080, alternative
5. Click **Next**
6. Select the **Android Automotive** system image you downloaded (API 34)
7. Click **Next**
8. Set the AVD name to `Honda_Infotainment` (or your preferred name)
9. Under **Emulated Performance → Graphics**, select **Hardware - GLES 2.0**
10. Click **Show Advanced Settings**:
    - RAM: **4096 MB**
    - Internal Storage: **4096 MB**
    - Orientation: **Landscape**
11. Click **Finish**

### Step 3: Configure the Honda App in the Emulator

Once the AVD is created and booted:

1. **Install the Honda infotainment APK** (if you have one):
   ```bash
   adb install path/to/honda-infotainment.apk
   ```

2. **Or configure your app as the default launcher** by updating the emulator's system:
   ```bash
   # Push your app config
   adb push honda_config.xml /data/local/tmp/
   ```

3. **Set the mock service endpoint** in your Honda app's configuration:
   - If the app reads from a config file:
     ```bash
     adb shell "echo 'backend_url=http://127.0.0.1:5100' > /data/local/tmp/sil_config.properties"
     ```
   - If the app uses system properties:
     ```bash
     adb shell setprop persist.honda.sil.backend_url http://127.0.0.1:5100
     ```
   - If the app reads environment variables, set them in the app's launch config

## Network Architecture

```
┌─────────────────────────────────────────────────────────┐
│  macOS Host                                             │
│                                                         │
│  ┌──────────────────┐       ┌────────────────────────┐  │
│  │  SIL Mock Service│       │  AskUI Agent           │  │
│  │  :5100           │       │  (python main.py)      │  │
│  └────────┬─────────┘       └───────────┬────────────┘  │
│           │                             │               │
│           │ HTTP                         │ screen/mouse  │
│           │                             │               │
│  ┌────────┴─────────────────────────────┴────────────┐  │
│  │  Android Studio Emulator Window                   │  │
│  │  ┌──────────────────────────────────────────────┐ │  │
│  │  │  Android Automotive OS                       │ │  │
│  │  │  ┌────────────────────────────────────────┐  │ │  │
│  │  │  │  Honda Infotainment App                │  │ │  │
│  │  │  │                                        │  │ │  │
│  │  │  │  Backend URL:                          │  │ │  │
│  │  │  │    http://127.0.0.1:5100               │  │ │  │
│  │  │  │    (via adb reverse)                   │  │ │  │
│  │  │  │  — or —                                │  │ │  │
│  │  │  │    http://10.0.2.2:5100                │  │ │  │
│  │  │  │    (Android emulator host alias)       │  │ │  │
│  │  │  └────────────────────────────────────────┘  │ │  │
│  │  └──────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### How the emulator reaches the mock service

Two options (both are set up by `start_sil.sh`):

1. **`adb reverse tcp:5100 tcp:5100`** — forwards the emulator's `localhost:5100` to the host's `localhost:5100`. The Honda app can use `http://127.0.0.1:5100`.

2. **`10.0.2.2`** — Android emulator's built-in alias for the host machine's loopback. The Honda app can use `http://10.0.2.2:5100`. No ADB setup required, but only works in the standard Android emulator.

## Troubleshooting

### Emulator won't boot
- Ensure hardware acceleration is enabled: **Android Studio → Settings → check "Use Host GPU"**
- On Apple Silicon: use `arm64-v8a` system images, not `x86_64`
- Try `./emulator/start_sil.sh` with `-no-snapshot-load` (already included)

### Mock service not reachable from emulator
```bash
# Verify ADB sees the emulator
adb devices

# Re-apply port forwarding
adb reverse tcp:5100 tcp:5100

# Test from inside the emulator
adb shell curl http://127.0.0.1:5100/status

# If curl isn't available in the emulator, test the host alias
adb shell ping -c 1 10.0.2.2
```

### Honda app doesn't show mock data
- Confirm the app is configured to point at `http://127.0.0.1:5100` or `http://10.0.2.2:5100`
- Check the mock service is running: `curl http://127.0.0.1:5100/status`
- Check mock data is loaded: `curl http://127.0.0.1:5100/bluetooth`
- Reset fixtures: `curl -X POST http://127.0.0.1:5100/reset`

### AskUI can't interact with the emulator
- macOS **Screen Recording** and **Accessibility** permissions must be granted to your terminal
- The emulator window must be visible and not minimized
- Disable macOS notification center / Focus mode during test runs
- If using multiple displays, keep the emulator on the primary display
