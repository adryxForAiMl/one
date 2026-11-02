from aerosim.missions.mission_manager import MissionManager, MissionStatus


def test_mission_manager_lifecycle():
    mm = MissionManager(acceptance_radius=2.0)
    wps = [
        {"latitude": 28.6130, "longitude": 77.2295, "altitude": 10.0, "loiter_time": 0.0},
        {"latitude": 28.6135, "longitude": 77.2300, "altitude": 15.0, "loiter_time": 0.0},
    ]

    mm.set_waypoints(wps)
    assert len(mm.waypoints) == 2
    assert mm.status == MissionStatus.IDLE

    started = mm.start()
    assert started
    assert mm.status == MissionStatus.RUNNING

    # Step to first WP
    target = mm.get_target_waypoint()
    assert target is not None
    assert target.id == 1

    # Simulate drone reaching first WP
    reached_target = mm.update(28.6130, 77.2295, 10.0)
    # Should advance to WP 2
    assert mm.current_wp_index == 1
