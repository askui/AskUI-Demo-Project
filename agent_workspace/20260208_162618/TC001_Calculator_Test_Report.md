# Test Execution Report

## Test Case Information
- **Test Case ID**: TC001
- **Test Case Name**: Calculator Subtraction 20-10
- **Execution Date**: February 08, 2026
- **Start Time**: 15:26:24 UTC
- **End Time**: 15:28:55 UTC
- **Total Execution Time**: ~2 minutes 31 seconds

## Test Environment
- **Platform**: macOS desktop
- **Application Under Test**: macOS Calculator app
- **Test Automation Tool**: AskUI Agent

## Test Steps Executed

### Step 1: Open the Calculator app
- **Action**: Used Spotlight search (Cmd+Space) to open Calculator
- **Expected Result**: Calculator app opens successfully
- **Actual Result**: ✅ Calculator app opened successfully
- **Screenshot**: step1_calculator_opened.png
- **Status**: PASSED

### Step 2: Click the "2" button
- **Action**: Clicked the "2" button on the calculator
- **Expected Result**: 2 is displayed in the calculator
- **Actual Result**: ✅ "2" displayed correctly
- **Screenshot**: step2_clicked_2.png
- **Status**: PASSED

### Step 3: Click the "0" button
- **Action**: Clicked the "0" button on the calculator
- **Expected Result**: 20 is displayed in the calculator
- **Actual Result**: ✅ "20" displayed correctly
- **Screenshot**: step3_clicked_0.png
- **Status**: PASSED

### Step 4: Click the "−" (minus) button
- **Action**: Clicked the minus operator button
- **Expected Result**: Minus operator is selected
- **Actual Result**: ✅ Calculator shows "20-" indicating minus operator selected
- **Screenshot**: step4_clicked_minus_corrected.png
- **Status**: PASSED

### Step 5: Click the "1" button
- **Action**: Clicked the "1" button
- **Expected Result**: 1 is displayed after the minus sign
- **Actual Result**: ✅ Calculator shows "20-1"
- **Screenshot**: step5_clicked_1.png
- **Status**: PASSED

### Step 6: Click the "0" button
- **Action**: Clicked the "0" button to complete "10"
- **Expected Result**: 10 is displayed after the minus sign
- **Actual Result**: ✅ Calculator shows "20-10"
- **Screenshot**: step6_clicked_0_complete.png
- **Status**: PASSED

### Step 7: Click the "=" button
- **Action**: Clicked the equals button to execute the calculation
- **Expected Result**: The result 10 is displayed
- **Actual Result**: ✅ Calculator displays:
  - Top line: "20-10" (calculation)
  - Bottom line: "10" (result)
- **Screenshot**: step7_clicked_equals_result.png
- **Status**: PASSED

### Step 8: Verify that the displayed result is 10
- **Action**: Verification of the final result
- **Expected Result**: Result shows 10 — test passed
- **Actual Result**: ✅ The calculator correctly displays "10" as the result
- **Status**: PASSED

## Test Summary
- **Total Test Steps**: 8
- **Steps Passed**: 8
- **Steps Failed**: 0
- **Overall Test Result**: ✅ PASSED

## Observations
1. All calculator buttons responded correctly to mouse clicks
2. The calculator display updated appropriately after each input
3. The subtraction operation (20 - 10) was calculated correctly
4. The result (10) was displayed clearly and accurately
5. No unexpected behaviors or errors were observed during test execution

## Screenshots Captured
- initial_state.png - Desktop before opening calculator
- step1_calculator_opened.png - Calculator app successfully opened
- step2_clicked_2.png - After entering "2"
- step3_clicked_0.png - After entering "20"
- step4_clicked_minus_corrected.png - After selecting minus operator
- step5_clicked_1.png - After entering "20-1"
- step6_clicked_0_complete.png - After entering complete expression "20-10"
- step7_clicked_equals_result.png - Final result showing "10"

## Conclusion
Test Case TC001 (Calculator Subtraction 20-10) has been executed successfully. All steps passed and the calculator performed the subtraction operation correctly, returning the expected result of 10. The macOS Calculator app is functioning as expected for basic subtraction operations.
