# Navigation Test Setup

1. Use the `sil_mock_service` tool to call `POST navigation/gps` with body `{"latitude": 37.3861, "longitude": -122.0839, "speed_kmh": 0}` to set the simulated GPS position to Mountain View, CA
2. Use the `sil_mock_service` tool to call `GET navigation` to verify POI data and saved destinations are loaded
3. From the Home screen, tap the "Navigation" icon to open the Navigation screen
4. Wait for the map to fully load and render
5. Verify the Navigation screen is displayed with a map view and search controls
