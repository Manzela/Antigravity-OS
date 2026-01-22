def test_simulated_crash():
    """
    Simulates a critical runtime error to trigger the Antigravity Flight Recorder.
    This test is EXPECTED TO FAIL.
    """
    # Simulate a complex logic failure that requires "thinking" to fix
    val = 100
    divisor = 0
    print(f"🚀 Initiating Launch Sequence... Target Altitude: {val}")
    
    # CRITICAL FAILURE - FIXED
    if divisor == 0:
        altitude = 0
    else:
        altitude = val / divisor
    
    assert altitude >= 0
