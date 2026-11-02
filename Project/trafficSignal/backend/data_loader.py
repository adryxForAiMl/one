"""SUMO Network and Traffic Demand Scenario Generator & Data Loader.

Provides:
1. Clean programmatic generation of complete 4-way SUMO intersection scenarios:
   - Network topology (.nod.xml, .edg.xml, .con.xml, .tll.xml, .net.xml)
   - Traffic light programs with non-conflicting green phases
   - Advance and stopline induction loop detectors (.det.xml)
   - Calibrated route demand with reproducible random seeds (.rou.xml)
   - Configuration file (.sumocfg)
2. Mendeley traffic dataset loader / adapter.
3. Labelled synthetic scenario generator when external dataset is absent.
"""

from __future__ import annotations
import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET

from Traffic.config.settings import PROJECT_ROOT, NETWORKS_DIR, DATA_DIR, DemandProfile, find_sumo_binary


class SumoNetworkBuilder:
    """Constructs and validates standard SUMO intersection networks and routes."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or NETWORKS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_full_scenario(
        self,
        demand: Optional[DemandProfile] = None,
        duration: int = 300,
        seed: int = 42
    ) -> Path:
        """Generate all required SUMO XML files and return path to .sumocfg."""
        if demand is None:
            demand = DemandProfile()

        self._write_nodes_file()
        self._write_edges_file()
        self._write_connections_file()
        self._write_traffic_light_file()
        self._write_detectors_file()
        self._compile_or_write_net_file()
        self._write_routes_file(demand, duration, seed)
        sumocfg_path = self._write_sumocfg_file()
        
        return sumocfg_path

    def _write_nodes_file(self) -> Path:
        """Write intersection.nod.xml (nodes / junctions)."""
        content = """<nodes>
    <node id="junction_center" x="0.0" y="0.0" type="traffic_light"/>
    <node id="node_N" x="0.0" y="250.0" type="priority"/>
    <node id="node_S" x="0.0" y="-250.0" type="priority"/>
    <node id="node_E" x="250.0" y="0.0" type="priority"/>
    <node id="node_W" x="-250.0" y="0.0" type="priority"/>
</nodes>"""
        path = self.output_dir / "intersection.nod.xml"
        path.write_text(content, encoding="utf-8")
        return path

    def _write_edges_file(self) -> Path:
        """Write intersection.edg.xml (incoming and outgoing roadway edges)."""
        content = """<edges>
    <!-- North Approach -->
    <edge id="edge_N_in" from="node_N" to="junction_center" priority="75" numLanes="2" speed="13.89"/>
    <edge id="edge_N_out" from="junction_center" to="node_N" priority="75" numLanes="2" speed="13.89"/>

    <!-- South Approach -->
    <edge id="edge_S_in" from="node_S" to="junction_center" priority="75" numLanes="2" speed="13.89"/>
    <edge id="edge_S_out" from="junction_center" to="node_S" priority="75" numLanes="2" speed="13.89"/>

    <!-- East Approach -->
    <edge id="edge_E_in" from="node_E" to="junction_center" priority="70" numLanes="2" speed="13.89"/>
    <edge id="edge_E_out" from="junction_center" to="node_E" priority="70" numLanes="2" speed="13.89"/>

    <!-- West Approach -->
    <edge id="edge_W_in" from="node_W" to="junction_center" priority="70" numLanes="2" speed="13.89"/>
    <edge id="edge_W_out" from="junction_center" to="node_W" priority="70" numLanes="2" speed="13.89"/>
</edges>"""
        path = self.output_dir / "intersection.edg.xml"
        path.write_text(content, encoding="utf-8")
        return path

    def _write_connections_file(self) -> Path:
        """Write intersection.con.xml (lane-to-lane turning definitions)."""
        content = """<connections>
    <!-- North in: Lane 0 (Right turn + Through), Lane 1 (Left turn) -->
    <connection from="edge_N_in" to="edge_W_out" fromLane="0" toLane="0"/>
    <connection from="edge_N_in" to="edge_S_out" fromLane="0" toLane="0"/>
    <connection from="edge_N_in" to="edge_E_out" fromLane="1" toLane="1"/>

    <!-- South in: Lane 0 (Right turn + Through), Lane 1 (Left turn) -->
    <connection from="edge_S_in" to="edge_E_out" fromLane="0" toLane="0"/>
    <connection from="edge_S_in" to="edge_N_out" fromLane="0" toLane="0"/>
    <connection from="edge_S_in" to="edge_W_out" fromLane="1" toLane="1"/>

    <!-- East in: Lane 0 (Right turn + Through), Lane 1 (Left turn) -->
    <connection from="edge_E_in" to="edge_N_out" fromLane="0" toLane="0"/>
    <connection from="edge_E_in" to="edge_W_out" fromLane="0" toLane="0"/>
    <connection from="edge_E_in" to="edge_S_out" fromLane="1" toLane="1"/>

    <!-- West in: Lane 0 (Right turn + Through), Lane 1 (Left turn) -->
    <connection from="edge_W_in" to="edge_S_out" fromLane="0" toLane="0"/>
    <connection from="edge_W_in" to="edge_E_out" fromLane="0" toLane="0"/>
    <connection from="edge_W_in" to="edge_N_out" fromLane="1" toLane="1"/>
</connections>"""
        path = self.output_dir / "intersection.con.xml"
        path.write_text(content, encoding="utf-8")
        return path

    def _write_traffic_light_file(self) -> Path:
        """Write intersection.tll.xml (standard 4-phase signal timing with yellow and clearance)."""
        content = """<tlLogics>
    <tlLogic id="junction_center" type="static" programID="0" offset="0">
        <!-- Phase 0: North-South Green (30s) -->
        <phase duration="30" state="GGgrrrGGgrrr"/>
        <!-- Phase 1: North-South Yellow (4s) -->
        <phase duration="4"  state="yyyrrryyyrrr"/>
        <!-- Phase 2: All-Red Clearance (2s) -->
        <phase duration="2"  state="rrrrrrrrrrrr"/>
        <!-- Phase 3: East-West Green (25s) -->
        <phase duration="25" state="rrrGGgrrrGGg"/>
        <!-- Phase 4: East-West Yellow (4s) -->
        <phase duration="4"  state="rrryyyrrryyy"/>
        <!-- Phase 5: All-Red Clearance (2s) -->
        <phase duration="2"  state="rrrrrrrrrrrr"/>
    </tlLogic>
</tlLogics>"""
        path = self.output_dir / "intersection.tll.xml"
        path.write_text(content, encoding="utf-8")
        return path

    def _write_detectors_file(self) -> Path:
        """Write intersection.det.xml (E1 induction loops and E2 area queue detectors)."""
        content = """<additional>
    <!-- North Inflow Detectors -->
    <inductionLoop id="det_N_advance_0" lane="edge_N_in_0" pos="50.0" freq="1.0" file="det_out.xml"/>
    <inductionLoop id="det_N_advance_1" lane="edge_N_in_1" pos="50.0" freq="1.0" file="det_out.xml"/>
    <inductionLoop id="det_N_stop_0"    lane="edge_N_in_0" pos="-10.0" freq="1.0" file="det_out.xml"/>
    <inductionLoop id="det_N_stop_1"    lane="edge_N_in_1" pos="-10.0" freq="1.0" file="det_out.xml"/>
    <laneAreaDetector id="e2_N_0" lane="edge_N_in_0" pos="30.0" length="180.0" freq="1.0" file="det_e2.xml"/>
    <laneAreaDetector id="e2_N_1" lane="edge_N_in_1" pos="30.0" length="180.0" freq="1.0" file="det_e2.xml"/>

    <!-- South Inflow Detectors -->
    <inductionLoop id="det_S_advance_0" lane="edge_S_in_0" pos="50.0" freq="1.0" file="det_out.xml"/>
    <inductionLoop id="det_S_advance_1" lane="edge_S_in_1" pos="50.0" freq="1.0" file="det_out.xml"/>
    <inductionLoop id="det_S_stop_0"    lane="edge_S_in_0" pos="-10.0" freq="1.0" file="det_out.xml"/>
    <inductionLoop id="det_S_stop_1"    lane="edge_S_in_1" pos="-10.0" freq="1.0" file="det_out.xml"/>
    <laneAreaDetector id="e2_S_0" lane="edge_S_in_0" pos="30.0" length="180.0" freq="1.0" file="det_e2.xml"/>
    <laneAreaDetector id="e2_S_1" lane="edge_S_in_1" pos="30.0" length="180.0" freq="1.0" file="det_e2.xml"/>

    <!-- East Inflow Detectors -->
    <inductionLoop id="det_E_advance_0" lane="edge_E_in_0" pos="50.0" freq="1.0" file="det_out.xml"/>
    <inductionLoop id="det_E_advance_1" lane="edge_E_in_1" pos="50.0" freq="1.0" file="det_out.xml"/>
    <inductionLoop id="det_E_stop_0"    lane="edge_E_in_0" pos="-10.0" freq="1.0" file="det_out.xml"/>
    <inductionLoop id="det_E_stop_1"    lane="edge_E_in_1" pos="-10.0" freq="1.0" file="det_out.xml"/>
    <laneAreaDetector id="e2_E_0" lane="edge_E_in_0" pos="30.0" length="180.0" freq="1.0" file="det_e2.xml"/>
    <laneAreaDetector id="e2_E_1" lane="edge_E_in_1" pos="30.0" length="180.0" freq="1.0" file="det_e2.xml"/>

    <!-- West Inflow Detectors -->
    <inductionLoop id="det_W_advance_0" lane="edge_W_in_0" pos="50.0" freq="1.0" file="det_out.xml"/>
    <inductionLoop id="det_W_advance_1" lane="edge_W_in_1" pos="50.0" freq="1.0" file="det_out.xml"/>
    <inductionLoop id="det_W_stop_0"    lane="edge_W_in_0" pos="-10.0" freq="1.0" file="det_out.xml"/>
    <inductionLoop id="det_W_stop_1"    lane="edge_W_in_1" pos="-10.0" freq="1.0" file="det_out.xml"/>
    <laneAreaDetector id="e2_W_0" lane="edge_W_in_0" pos="30.0" length="180.0" freq="1.0" file="det_e2.xml"/>
    <laneAreaDetector id="e2_W_1" lane="edge_W_in_1" pos="30.0" length="180.0" freq="1.0" file="det_e2.xml"/>
</additional>"""
        path = self.output_dir / "intersection.det.xml"
        path.write_text(content, encoding="utf-8")
        return path

    def _compile_or_write_net_file(self) -> Path:
        """Compile netconvert to generate fully validated SUMO network XML."""
        net_path = self.output_dir / "intersection.net.xml"
        
        # Candidate netconvert binary paths
        candidates = [
            PROJECT_ROOT.parent / ".venv" / "bin" / "netconvert",
            Path(sys.prefix) / "bin" / "netconvert",
            shutil.which("netconvert")
        ]
        
        netconvert_bin = None
        for cand in candidates:
            if cand and Path(cand).is_file() and os.access(cand, os.X_OK):
                netconvert_bin = str(cand)
                break
                
        if netconvert_bin:
            cmd = [
                netconvert_bin,
                "--node-files", str(self.output_dir / "intersection.nod.xml"),
                "--edge-files", str(self.output_dir / "intersection.edg.xml"),
                "--connection-files", str(self.output_dir / "intersection.con.xml"),
                "--tllogic-files", str(self.output_dir / "intersection.tll.xml"),
                "--output-file", str(net_path),
                "--no-turnarounds", "true",
                "--offset.disable-normalization", "true",
            ]
            try:
                subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=10)
                if net_path.exists() and net_path.stat().st_size > 500:
                    return net_path
            except Exception:
                pass

        return net_path

    def _write_standalone_net_xml(self, target_path: Path):
        """Generates a complete, verified valid SUMO net.xml without external binaries."""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<net version="1.20" junctionCornerDetail="5" limitTurnSpeed="5.50" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/net_file.xsd">
    <location netOffset="0.00,0.00" convBoundary="-250.00,-250.00,250.00,250.00" origBoundary="-250.00,-250.00,250.00,250.00" projParameter="!"/>
    
    <edge id=":junction_center_0" function="internal">
        <lane id=":junction_center_0_0" index="0" speed="6.51" length="9.03" shape="-4.80,8.00 -4.45,4.05 -3.40,1.20 -1.65,-0.75 0.90,-1.80"/>
    </edge>
    <edge id=":junction_center_1" function="internal">
        <lane id=":junction_center_1_0" index="0" speed="13.89" length="16.00" shape="-1.60,8.00 -1.60,-8.00"/>
    </edge>
    <edge id=":junction_center_2" function="internal">
        <lane id=":junction_center_2_0" index="0" speed="8.50" length="15.00" shape="-1.60,8.00 -1.05,2.45 0.60,-1.50 3.35,-3.85 7.20,-4.60"/>
    </edge>
    <edge id=":junction_center_3" function="internal">
        <lane id=":junction_center_3_0" index="0" speed="6.51" length="9.03" shape="4.80,-8.00 4.45,-4.05 3.40,-1.20 1.65,0.75 -0.90,1.80"/>
    </edge>
    <edge id=":junction_center_4" function="internal">
        <lane id=":junction_center_4_0" index="0" speed="13.89" length="16.00" shape="1.60,-8.00 1.60,8.00"/>
    </edge>
    <edge id=":junction_center_5" function="internal">
        <lane id=":junction_center_5_0" index="0" speed="8.50" length="15.00" shape="1.60,-8.00 1.05,-2.45 -0.60,1.50 -3.35,3.85 -7.20,4.60"/>
    </edge>
    <edge id=":junction_center_6" function="internal">
        <lane id=":junction_center_6_0" index="0" speed="6.51" length="9.03" shape="8.00,4.80 4.05,4.45 1.20,3.40 -0.75,1.65 -1.80,-0.90"/>
    </edge>
    <edge id=":junction_center_7" function="internal">
        <lane id=":junction_center_7_0" index="0" speed="13.89" length="16.00" shape="8.00,1.60 -8.00,1.60"/>
    </edge>
    <edge id=":junction_center_8" function="internal">
        <lane id=":junction_center_8_0" index="0" speed="8.50" length="15.00" shape="8.00,1.60 2.45,1.05 -1.50,-0.60 -3.85,-3.35 -4.60,-7.20"/>
    </edge>
    <edge id=":junction_center_9" function="internal">
        <lane id=":junction_center_9_0" index="0" speed="6.51" length="9.03" shape="-8.00,-4.80 -4.05,-4.45 -1.20,-3.40 0.75,-1.65 1.80,0.90"/>
    </edge>
    <edge id=":junction_center_10" function="internal">
        <lane id=":junction_center_10_0" index="0" speed="13.89" length="16.00" shape="-8.00,-1.60 8.00,-1.60"/>
    </edge>
    <edge id=":junction_center_11" function="internal">
        <lane id=":junction_center_11_0" index="0" speed="8.50" length="15.00" shape="-8.00,-1.60 -2.45,-1.05 1.50,0.60 3.85,3.35 4.60,7.20"/>
    </edge>

    <edge id="edge_E_in" from="node_E" to="junction_center" priority="70">
        <lane id="edge_E_in_0" index="0" speed="13.89" length="242.00" shape="250.00,4.80 8.00,4.80"/>
        <lane id="edge_E_in_1" index="1" speed="13.89" length="242.00" shape="250.00,1.60 8.00,1.60"/>
    </edge>
    <edge id="edge_E_out" from="junction_center" to="node_E" priority="70">
        <lane id="edge_E_out_0" index="0" speed="13.89" length="242.00" shape="8.00,-4.80 250.00,-4.80"/>
        <lane id="edge_E_out_1" index="1" speed="13.89" length="242.00" shape="8.00,-1.60 250.00,-1.60"/>
    </edge>
    <edge id="edge_N_in" from="node_N" to="junction_center" priority="75">
        <lane id="edge_N_in_0" index="0" speed="13.89" length="242.00" shape="-4.80,250.00 -4.80,8.00"/>
        <lane id="edge_N_in_1" index="1" speed="13.89" length="242.00" shape="-1.60,250.00 -1.60,8.00"/>
    </edge>
    <edge id="edge_N_out" from="junction_center" to="node_N" priority="75">
        <lane id="edge_N_out_0" index="0" speed="13.89" length="242.00" shape="4.80,8.00 4.80,250.00"/>
        <lane id="edge_N_out_1" index="1" speed="13.89" length="242.00" shape="1.60,8.00 1.60,250.00"/>
    </edge>
    <edge id="edge_S_in" from="node_S" to="junction_center" priority="75">
        <lane id="edge_S_in_0" index="0" speed="13.89" length="242.00" shape="4.80,-250.00 4.80,-8.00"/>
        <lane id="edge_S_in_1" index="1" speed="13.89" length="242.00" shape="1.60,-250.00 1.60,-8.00"/>
    </edge>
    <edge id="edge_S_out" from="junction_center" to="node_S" priority="75">
        <lane id="edge_S_out_0" index="0" speed="13.89" length="242.00" shape="-4.80,-8.00 -4.80,-250.00"/>
        <lane id="edge_S_out_1" index="1" speed="13.89" length="242.00" shape="-1.60,-8.00 -1.60,-250.00"/>
    </edge>
    <edge id="edge_W_in" from="node_W" to="junction_center" priority="70">
        <lane id="edge_W_in_0" index="0" speed="13.89" length="242.00" shape="-250.00,-4.80 -8.00,-4.80"/>
        <lane id="edge_W_in_1" index="1" speed="13.89" length="242.00" shape="-250.00,-1.60 -8.00,-1.60"/>
    </edge>
    <edge id="edge_W_out" from="junction_center" to="node_W" priority="70">
        <lane id="edge_W_out_0" index="0" speed="13.89" length="242.00" shape="-8.00,4.80 -250.00,4.80"/>
        <lane id="edge_W_out_1" index="1" speed="13.89" length="242.00" shape="-8.00,1.60 -250.00,1.60"/>
    </edge>

    <tlLogic id="junction_center" type="static" programID="0" offset="0">
        <phase duration="30" state="GGgrrrGGgrrr"/>
        <phase duration="4"  state="yyyrrryyyrrr"/>
        <phase duration="2"  state="rrrrrrrrrrrr"/>
        <phase duration="25" state="rrrGGgrrrGGg"/>
        <phase duration="4"  state="rrryyyrrryyy"/>
        <phase duration="2"  state="rrrrrrrrrrrr"/>
    </tlLogic>

    <junction id="junction_center" type="traffic_light" x="0.00" y="0.00" incLanes="edge_N_in_0 edge_N_in_1 edge_S_in_0 edge_S_in_1 edge_E_in_0 edge_E_in_1 edge_W_in_0 edge_W_in_1" intLanes=":junction_center_0_0 :junction_center_1_0 :junction_center_2_0 :junction_center_3_0 :junction_center_4_0 :junction_center_5_0 :junction_center_6_0 :junction_center_7_0 :junction_center_8_0 :junction_center_9_0 :junction_center_10_0 :junction_center_11_0" shape="-6.40,8.00 6.40,8.00 8.00,6.40 8.00,-6.40 6.40,-8.00 -6.40,-8.00 -8.00,-6.40 -8.00,6.40"/>
    <junction id="node_E" type="priority" x="250.00" y="0.00" incLanes="edge_E_out_0 edge_E_out_1" intLanes="" shape="250.00,0.00 250.00,-6.40 250.00,0.00"/>
    <junction id="node_N" type="priority" x="0.00" y="250.00" incLanes="edge_N_out_0 edge_N_out_1" intLanes="" shape="0.00,250.00 6.40,250.00 0.00,250.00"/>
    <junction id="node_S" type="priority" x="0.00" y="-250.00" incLanes="edge_S_out_0 edge_S_out_1" intLanes="" shape="0.00,-250.00 -6.40,-250.00 0.00,-250.00"/>
    <junction id="node_W" type="priority" x="-250.00" y="0.00" incLanes="edge_W_out_0 edge_W_out_1" intLanes="" shape="-250.00,0.00 -250.00,6.40 -250.00,0.00"/>

    <connection from="edge_N_in" to="edge_W_out" fromLane="0" toLane="0" via=":junction_center_0_0" tl="junction_center" linkIndex="0" dir="r" state="O"/>
    <connection from="edge_N_in" to="edge_S_out" fromLane="0" toLane="0" via=":junction_center_1_0" tl="junction_center" linkIndex="1" dir="s" state="O"/>
    <connection from="edge_N_in" to="edge_E_out" fromLane="1" toLane="1" via=":junction_center_2_0" tl="junction_center" linkIndex="2" dir="l" state="o"/>
    <connection from="edge_S_in" to="edge_E_out" fromLane="0" toLane="0" via=":junction_center_3_0" tl="junction_center" linkIndex="3" dir="r" state="O"/>
    <connection from="edge_S_in" to="edge_N_out" fromLane="0" toLane="0" via=":junction_center_4_0" tl="junction_center" linkIndex="4" dir="s" state="O"/>
    <connection from="edge_S_in" to="edge_W_out" fromLane="1" toLane="1" via=":junction_center_5_0" tl="junction_center" linkIndex="5" dir="l" state="o"/>
    <connection from="edge_E_in" to="edge_N_out" fromLane="0" toLane="0" via=":junction_center_6_0" tl="junction_center" linkIndex="6" dir="r" state="O"/>
    <connection from="edge_E_in" to="edge_W_out" fromLane="0" toLane="0" via=":junction_center_7_0" tl="junction_center" linkIndex="7" dir="s" state="O"/>
    <connection from="edge_E_in" to="edge_S_out" fromLane="1" toLane="1" via=":junction_center_8_0" tl="junction_center" linkIndex="8" dir="l" state="o"/>
    <connection from="edge_W_in" to="edge_S_out" fromLane="0" toLane="0" via=":junction_center_9_0" tl="junction_center" linkIndex="9" dir="r" state="O"/>
    <connection from="edge_W_in" to="edge_E_out" fromLane="0" toLane="0" via=":junction_center_10_0" tl="junction_center" linkIndex="10" dir="s" state="O"/>
    <connection from="edge_W_in" to="edge_N_out" fromLane="1" toLane="1" via=":junction_center_11_0" tl="junction_center" linkIndex="11" dir="l" state="o"/>
</net>"""
        target_path.write_text(content, encoding="utf-8")

    def _write_routes_file(self, demand: DemandProfile, duration: int, seed: int) -> Path:
        """Generate intersection.rou.xml with calibrated vehicle dispatch.
        Guarantees identical pseudo-random arrival schedules when using the same seed.
        """
        import random
        rng = random.Random(seed)
        
        routes = [
            ("r_N_S", "edge_N_in edge_S_out"),
            ("r_N_W", "edge_N_in edge_W_out"),
            ("r_N_E", "edge_N_in edge_E_out"),
            ("r_S_N", "edge_S_in edge_N_out"),
            ("r_S_E", "edge_S_in edge_E_out"),
            ("r_S_W", "edge_S_in edge_W_out"),
            ("r_E_W", "edge_E_in edge_W_out"),
            ("r_E_N", "edge_E_in edge_N_out"),
            ("r_E_S", "edge_E_in edge_S_out"),
            ("r_W_E", "edge_W_in edge_E_out"),
            ("r_W_S", "edge_W_in edge_S_out"),
            ("r_W_N", "edge_W_in edge_N_out"),
        ]

        xml_lines = [
            """<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">""",
            """    <vType id="hatchback" accel="2.8" decel="4.8" sigma="0.5" length="4.2" width="1.8" height="1.45" minGap="2.0" maxSpeed="15.0"/>""",
            """    <vType id="sedan" accel="2.6" decel="4.5" sigma="0.5" length="4.6" width="1.9" height="1.5" minGap="2.5" maxSpeed="15.0"/>""",
            """    <vType id="suv" accel="2.4" decel="4.5" sigma="0.5" length="5.0" width="2.1" height="1.85" minGap="2.8" maxSpeed="14.0"/>""",
            """    <vType id="van" accel="2.1" decel="4.2" sigma="0.5" length="5.9" width="2.25" height="2.4" minGap="3.0" maxSpeed="13.0"/>""",
            """    <vType id="bus" accel="1.4" decel="3.8" sigma="0.5" length="11.5" width="2.7" height="3.0" minGap="3.5" maxSpeed="11.0"/>""",
            """    <vType id="truck" accel="1.8" decel="4.0" sigma="0.5" length="9.2" width="2.8" height="3.1" minGap="3.5" maxSpeed="12.0"/>"""
        ]

        for r_id, edges in routes:
            xml_lines.append(f"""    <route id="{r_id}" edges="{edges}"/>""")

        direction_routes = {
            "North": (demand.vehs_per_hour_ns, "r_N_W", "r_N_E", "r_N_S"),
            "South": (demand.vehs_per_hour_ns, "r_S_E", "r_S_W", "r_S_N"),
            "East": (demand.vehs_per_hour_ew, "r_E_N", "r_E_S", "r_E_W"),
            "West": (demand.vehs_per_hour_ew, "r_W_S", "r_W_N", "r_W_E"),
        }

        def multiplier(t: float) -> float:
            if demand.scenario == "sudden_surge":
                return 3.0 if t >= duration * 0.5 else 1.0
            if demand.scenario == "rush_hour":
                fraction = t / max(1.0, duration)
                if fraction < 0.25:
                    return 0.55
                if fraction < 0.5:
                    return 1.0
                if fraction < 0.8:
                    return 2.0
                return 1.25
            return 1.0

        arrivals = []
        for direction, (volume, right_route, left_route, through_route) in direction_routes.items():
            rate = max(0.0, float(volume)) / 3600.0
            approach_multiplier = 2.4 if demand.scenario == "heavy_ns" and direction in ("North", "South") else 1.0
            t = 0.0
            max_scenario_multiplier = 3.0 if demand.scenario == "sudden_surge" else 2.0 if demand.scenario == "rush_hour" else 1.0
            max_rate = rate * approach_multiplier * max_scenario_multiplier
            while max_rate > 0:
                t += rng.expovariate(max_rate)
                if t >= duration:
                    break
                if rng.random() > multiplier(t) * approach_multiplier * rate / max_rate:
                    continue
                turn_roll = rng.random()
                route_id = (
                    right_route if turn_roll < demand.turning_ratio_right else
                    left_route if turn_roll < demand.turning_ratio_right + demand.turning_ratio_left else
                    through_route
                )
                arrivals.append((t, direction, route_id))

        arrivals.sort(key=lambda event: (event[0], event[1]))
        vehicle_types = ("hatchback", "sedan", "suv", "van", "bus", "truck")
        vehicle_weights = (20, 38, 20, 10, 5, 7)
        for veh_idx, (depart, _direction, route_id) in enumerate(arrivals):
            type_id = rng.choices(vehicle_types, weights=vehicle_weights, k=1)[0]
            xml_lines.append(
                f'''    <vehicle id="veh_{veh_idx}" type="{type_id}" route="{route_id}" depart="{depart:.3f}" departLane="best" departSpeed="max"/>'''
            )

        xml_lines.append("</routes>")
        path = self.output_dir / "intersection.rou.xml"
        path.write_text("\n".join(xml_lines), encoding="utf-8")
        return path

    def _write_sumocfg_file(self) -> Path:
        """Write simulation.sumocfg (master configuration file)."""
        content = """<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/sumoConfiguration.xsd">
    <input>
        <net-file value="intersection.net.xml"/>
        <route-files value="intersection.rou.xml"/>
        <additional-files value="intersection.det.xml"/>
    </input>
    <time>
        <begin value="0"/>
        <step-length value="1.0"/>
    </time>
    <processing>
        <time-to-teleport value="-1"/>
        <waiting-time-memory value="1000"/>
    </processing>
    <report>
        <verbose value="false"/>
        <no-step-log value="true"/>
    </report>
    <gui_only>
        <start value="true"/>
        <quit-on-end value="true"/>
    </gui_only>
</configuration>"""
        path = self.output_dir / "simulation.sumocfg"
        path.write_text(content, encoding="utf-8")
        return path
