import xml.etree.ElementTree as ET

import traci

from Traffic.backend.data_loader import SumoNetworkBuilder
from Traffic.backend.simulation import AdaptiveController, FixedTimeController
from Traffic.config.settings import SignalTimingConfig


def test_generated_signal_program_has_separate_greens_and_clearance(tmp_path):
    builder = SumoNetworkBuilder(output_dir=tmp_path)
    builder.generate_full_scenario(duration=20, seed=9)
    root = ET.parse(tmp_path / "intersection.tll.xml").getroot()
    phases = root.findall(".//phase")
    assert len(phases) == 6
    states = [phase.attrib["state"] for phase in phases]
    ns_green = {i for i, char in enumerate(states[0]) if char in "Gg"}
    ew_green = {i for i, char in enumerate(states[3]) if char in "Gg"}
    assert ns_green and ew_green
    assert ns_green.isdisjoint(ew_green)
    assert set(states[1][i] for i in ns_green) == {"y"}
    assert set(states[4][i] for i in ew_green) == {"y"}
    assert set(states[2]) == {"r"}
    assert set(states[5]) == {"r"}


def test_controllers_keep_green_yellow_all_red_sequence(monkeypatch):
    phase_writes = []
    monkeypatch.setattr(traci.trafficlight, "setPhase", lambda tls, phase: phase_writes.append(phase))
    monkeypatch.setattr(traci.trafficlight, "setPhaseDuration", lambda *args: None)
    config = SignalTimingConfig()
    controllers = [FixedTimeController(config=config), AdaptiveController(config=config)]

    for controller in controllers:
        if isinstance(controller, AdaptiveController):
            controller.optimize_new_cycle = lambda _queues: None
            advance = lambda: controller.step(1.0, {})
            green_lengths = (controller.current_allocated_green_ns, controller.current_allocated_green_ew)
        else:
            advance = lambda: controller.step(1.0)
            green_lengths = (controller.phase_schedule[0][1], controller.phase_schedule[3][1])
        assert all(config.min_green <= value <= config.max_green for value in green_lengths)
        phase_writes.clear()
        for _ in range(6):
            controller.time_in_phase = controller.get_phase_duration(controller.current_phase) if isinstance(controller, AdaptiveController) else controller.phase_schedule[controller.current_idx][1]
            advance()
        assert phase_writes == [1, 2, 3, 4, 5, 0]
        assert config.yellow_time == 4.0
        assert config.all_red_time == 2.0
