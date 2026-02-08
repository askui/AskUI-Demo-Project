# Calculator Test Execution Report

## Test Case Information
- **Test Case ID**: TC001
- **Test Case Name**: Calculator Subtraction 20-10
- **Execution Date**: February 8, 2026
- **Execution Status**: ✅ PASSED

## Test Steps Execution Summary

| Step | Description | Expected Result | Actual Result | Status | Screenshot |
|------|-------------|----------------|---------------|---------|------------|
| 1 | Open the Calculator app on this Mac | Calculator app opens successfully | Calculator was already open and ready | ✅ PASSED | step_0_initial_state.png |
| 2 | Click the "2" button | 2 is displayed in the calculator | "2" displayed correctly | ✅ PASSED | step_2_click_button_2.png |
| 3 | Click the "0" button | 20 is displayed in the calculator | "20" displayed correctly | ✅ PASSED | step_3_click_button_0.png |
| 4 | Click the "−" (minus) button | Minus operator is selected | "20-" displayed, minus operator selected | ✅ PASSED | step_4_click_minus_button.png |
| 5 | Click the "1" button | 1 is displayed after the minus sign | "20-1" displayed correctly | ✅ PASSED | step_5_click_button_1.png |
| 6 | Click the "0" button | 10 is displayed after the minus sign | "20-10" displayed correctly | ✅ PASSED | step_6_click_button_0_second_time.png |
| 7 | Click the "=" button | The result 10 is displayed | Result "10" displayed with calculation "20-10" shown above | ✅ PASSED | step_7_click_equals_button.png |
| 8 | Verify that the displayed result is 10 | Result shows 10 — test passed | Verification confirmed: result is "10" | ✅ PASSED | step_7_click_equals_button.png |

## Detailed Execution Log

### Pre-Execution
- Checked for available cached trajectories: None found
- Calculator app was already open and ready for testing

### Step-by-Step Execution
1. **Initial State**: Calculator app displayed with "0" showing
2. **Number Entry**: Successfully entered "20" by clicking "2" then "0"
3. **Operator Selection**: Successfully selected minus (-) operator, display showed "20-"
4. **Second Number Entry**: Successfully entered "10" by clicking "1" then "0", display showed "20-10"
5. **Calculation**: Pressed equals (=) button and received correct result "10"
6. **Verification**: Confirmed the result matches expected value of 10

### Screenshots Captured
- step_0_initial_state.png - Initial calculator state
- step_2_click_button_2.png - After clicking "2"
- step_3_click_button_0.png - After clicking "0" (showing "20")
- step_4_click_minus_button.png - After clicking minus (showing "20-")
- step_5_click_button_1.png - After clicking "1" (showing "20-1")
- step_6_click_button_0_second_time.png - After clicking "0" (showing "20-10")
- step_7_click_equals_button.png - Final result showing "10"

## Test Results
- **Overall Status**: ✅ PASSED
- **All Steps Completed**: 8/8
- **All Assertions Passed**: ✅ Yes
- **Calculation Accuracy**: ✅ Correct (20-10=10)
- **UI Responsiveness**: ✅ Excellent
- **No Errors Encountered**: ✅ True

## Conclusion
The calculator subtraction test case TC001 executed successfully. All UI interactions worked as expected, and the mathematical calculation (20-10=10) was performed correctly. The test demonstrates that the macOS Calculator app properly handles basic subtraction operations with two-digit numbers.

## Technical Details
- **Platform**: macOS
- **Application**: Calculator (built-in macOS app)
- **Automation Tool**: AskUI Agent
- **Test Method**: Manual step-by-step UI interaction
- **Cache Usage**: No cached trajectories were available for this test case