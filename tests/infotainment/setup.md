# Infotainment SIL Setup

**Prerequisites:** The Android Studio emulator and SIL mock service must already be running. Start them with: `./emulator/start_sil.sh`

1. Use the `sil_mock_service` tool to call `GET status` and confirm the mock service is running
2. Use the `sil_mock_service` tool to call `POST reset` to reset all mock data to fixture defaults
3. Use the `sil_mock_service` tool to call `POST bluetooth/connect` with body `{"device_id": "bt-001"}` to pre-connect the iPhone for Phone and Bluetooth Audio tests
4. Verify the Android emulator window is visible on screen and has finished booting (Home screen or launcher is displayed)
5. Verify the Home screen shows the main menu icons (Audio, Navigation, Phone, Climate, Settings)
6. Take a screenshot to confirm the emulator is ready
