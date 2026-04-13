# Honda Infotainment SIL Testing Rules

- All tests are executed against the Honda infotainment emulator running on macOS
- Before interacting with any UI element, verify it is visible on the emulator screen
- After each action, wait for the emulator UI to finish any transition or loading animation before proceeding
- Take a screenshot after every significant interaction to document the emulator state
- If a test step fails, take a screenshot, record the failure, and continue with the remaining steps
- Always return to the Home screen between separate test cases unless the next test explicitly starts from the current screen
- Use the on-screen soft buttons for navigation (Home, Back, Menu) rather than keyboard shortcuts unless otherwise specified
- Text entry fields: click the field first to focus it, then type using keyboard input

## SIL Mock Service

A mock backend service runs at `http://127.0.0.1:5100` providing simulated vehicle data. You have the `sil_mock_service` tool to interact with it.

**Use the mock service to:**
- Set up preconditions before a test (e.g., connect a Bluetooth device, set GPS position)
- Verify backend state after a UI action (e.g., confirm the radio frequency changed)
- Reset state between test cases if needed (`POST reset`)

**Available domains:** bluetooth, radio, media, navigation, vehicle (climate is under vehicle)
