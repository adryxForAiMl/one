from aerosim.simulation.unified_flight_engine import UnifiedFlightEngine


def test_unified_engine_step_loop():
    engine = UnifiedFlightEngine()
    engine.arm()
    engine.set_flight_mode("AUTO_TAKEOFF")

    for _ in range(50):
        engine.update(0.02)

    telem = engine.get_telemetry_snapshot()
    assert telem["is_armed"] is True
    assert telem["flight_mode"] in ("AUTO_TAKEOFF", "POS_HOLD")
    assert telem["position"]["altitude_agl"] >= 0.15
    assert telem["battery"]["percentage"] <= 100.0


def test_unified_engine_reset():
    engine = UnifiedFlightEngine()
    engine.arm()
    engine.update(0.02)
    engine.reset_simulation()
    assert engine.autopilot.is_armed is False
    assert engine.physics.altitude == 0.15
