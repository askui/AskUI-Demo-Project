# Infotainment SIL Setup

1. Use the `sil_mock_service` tool to call `GET status` and confirm the mock service is running
2. Use the `sil_mock_service` tool to call `POST reset` to reset all mock data to fixture defaults
3. Use the `sil_mock_service` tool to call `POST bluetooth/connect` with body `{"device_id": "bt-001"}` to pre-connect the iPhone for Phone and Bluetooth Audio tests
4. Launch the Honda infotainment emulator application on macOS (if not already running)
5. Wait until the emulator has fully booted and the Home screen is displayed
6. Verify the Home screen shows the main menu icons (Audio, Navigation, Phone, Climate, Settings)
7. Take a screenshot to confirm the emulator is ready
