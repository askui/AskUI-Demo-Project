# Climate Control Test Setup

1. Use the `sil_mock_service` tool to call `GET vehicle` to verify climate mock data is loaded (driver temp, fan speed, A/C state)
2. Use the `sil_mock_service` tool to call `POST climate/temperature` with body `{"side": "driver", "temp_f": 72}` to ensure a known starting temperature
3. Use the `sil_mock_service` tool to call `POST climate/fan` with body `{"speed": 3}` to ensure a known starting fan speed
4. From the Home screen, tap the "Climate" icon to open the Climate Control screen
5. Wait for the Climate Control screen to fully load
6. Verify the Climate Control screen shows temperature controls, fan speed, and mode options
