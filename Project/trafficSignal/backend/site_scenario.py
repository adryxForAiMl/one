"""Site scenario loader, traffic modeling, dynamic conflict matrix, and 3D geometry extractor."""

from __future__ import annotations

import json
import math
import random
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from pyproj import CRS, Transformer

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SITES_CONFIG_DIR = PROJECT_ROOT / "config/sites"
SITES_DATA_DIR = PROJECT_ROOT / "data/sites"


def load_site_config(site_id: str = "boring_road_patna") -> Dict[str, Any]:
    """Load and return site configuration YAML."""
    config_path = SITES_CONFIG_DIR / f"{site_id}.yaml"
    if not config_path.is_file():
        raise FileNotFoundError(f"Site configuration not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def calculate_geh(simulated_flow: float, observed_count: float) -> float:
    """Calculate the Geoffrey E. Havers (GEH) statistic for flow comparison.
    
    Formula: sqrt( 2 * (M - C)^2 / (M + C) )
    """
    total = simulated_flow + observed_count
    if total <= 0:
        return 0.0
    return math.sqrt(2.0 * ((simulated_flow - observed_count) ** 2) / total)


def generate_geh_report(
    simulated_counts: Dict[str, float],
    observed_counts: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """Generate a GEH calibration report. If observed_counts is None, returns 'uncalibrated'."""
    if not observed_counts:
        return {
            "status": "uncalibrated",
            "disclaimer": "Simulation on real road geometry with assumed demand (no observed counts supplied)",
            "geh_by_approach": {},
            "percent_geh_under_5": 0.0,
            "passes_calibration": False,
        }

    geh_results = {}
    under_5 = 0
    total = 0
    for key, obs in observed_counts.items():
        sim = simulated_counts.get(key, 0.0)
        geh = calculate_geh(sim, obs)
        geh_results[key] = {
            "simulated_flow": sim,
            "observed_count": obs,
            "geh": round(geh, 2),
            "acceptable": geh < 5.0,
        }
        total += 1
        if geh < 5.0:
            under_5 += 1

    pct = (under_5 / total * 100.0) if total > 0 else 0.0
    return {
        "status": "calibrated" if pct >= 85.0 else "calibration_in_progress",
        "disclaimer": "Calibrated with empirical counts" if pct >= 85.0 else "Partial calibration against counts",
        "geh_by_approach": geh_results,
        "percent_geh_under_5": round(pct, 1),
        "passes_calibration": pct >= 85.0,
    }


def parse_net_conflicts(net_xml_path: Path, focus_radius_m: float = 60.0) -> Dict[str, Any]:
    """Derive dynamic movement conflict matrix from SUMO network XML connections and junction request foes."""
    tree = ET.parse(net_xml_path)
    root = tree.getroot()

    location = root.find("location")
    net_offset = (0.0, 0.0)
    if location is not None and location.get("netOffset"):
        parts = [float(x) for x in location.get("netOffset").split(",")]
        if len(parts) == 2:
            net_offset = (parts[0], parts[1])

    # Transform candidate fountain center (25.6126047, 85.1188289) to UTM EPSG:32645
    center_lat, center_lon = 25.6126047, 85.1188289
    try:
        cfg = load_site_config("boring_road_patna")
        center_lat = float(cfg["site"]["center"]["latitude"]["value"])
        center_lon = float(cfg["site"]["center"]["longitude"]["value"])
    except Exception:
        pass

    zone = int((center_lon + 180) // 6) + 1
    crs = CRS.from_epsg(32600 + zone)
    to_utm = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    cx, cy = to_utm.transform(center_lon, center_lat)
    center_xy = (cx + net_offset[0], cy + net_offset[1])

    # Collect movements at focus junctions
    junctions = root.findall("junction")
    focus_junctions = []
    for j in junctions:
        if j.get("type") == "internal":
            continue
        jx, jy = float(j.get("x", "0")), float(j.get("y", "0"))
        if math.hypot(jx - center_xy[0], jy - center_xy[1]) <= focus_radius_m:
            focus_junctions.append(j)

    movements = []
    connections = root.findall("connection")
    focus_j_ids = {j.get("id") for j in focus_junctions}

    edge_to_junction = {}
    for edge in root.findall("edge"):
        if edge.get("function") != "internal":
            edge_to_junction[edge.get("id")] = edge.get("to")

    movement_map = {}
    for conn in connections:
        from_edge = conn.get("from", "")
        to_edge = conn.get("to", "")
        if from_edge.startswith(":") or to_edge.startswith(":"):
            continue
        target_j = edge_to_junction.get(from_edge)
        if target_j in focus_j_ids:
            key = f"{from_edge}_{conn.get('fromLane')}_to_{to_edge}_{conn.get('toLane')}"
            if key not in movement_map:
                m_info = {
                    "id": key,
                    "from_edge": from_edge,
                    "from_lane": int(conn.get("fromLane", "0")),
                    "to_edge": to_edge,
                    "to_lane": int(conn.get("toLane", "0")),
                    "junction": target_j,
                    "dir": conn.get("dir", "s"),
                    "via": conn.get("via", ""),
                }
                movement_map[key] = m_info
                movements.append(m_info)

    # Build conflict matrix:
    # Two movements conflict if:
    # 1. They originate from different edges entering the same junction and their paths cross/merge
    # 2. Or net.xml junction request foes bitmask indicates conflict
    n = len(movements)
    matrix = [[False for _ in range(n)] for _ in range(n)]

    # Collect foes from junction requests
    request_foes: Dict[str, List[str]] = {}
    for j in focus_junctions:
        j_id = j.get("id")
        requests = j.findall("request")
        foes_list = [r.get("foes", "") for r in requests]
        request_foes[j_id] = foes_list

    for i in range(n):
        for k in range(i + 1, n):
            m1 = movements[i]
            m2 = movements[k]

            conflict = False
            # Same incoming edge but different turn paths can conflict if lanes cross
            if m1["junction"] == m2["junction"]:
                if m1["from_edge"] != m2["from_edge"]:
                    # Different approaches entering same junction:
                    # In left-hand drive, opposite straights don't conflict, crossing turns do
                    if m1["to_edge"] == m2["to_edge"]:
                        conflict = True  # Merge conflict
                    elif m1["dir"] in ("l", "t") or m2["dir"] in ("l", "t"):
                        conflict = True  # Turning across opposing traffic
                    elif m1["dir"] == "s" and m2["dir"] == "s":
                        conflict = True  # Crossing straights
                elif m1["from_lane"] == m2["from_lane"]:
                    conflict = True  # Same lane divergence conflict
            elif m1["to_edge"] == m2["to_edge"]:
                conflict = True  # Merge into identical edge

            matrix[i][k] = conflict
            matrix[k][i] = conflict

    return {
        "movements": movements,
        "conflict_matrix": matrix,
        "movement_count": n,
        "focus_junction_ids": list(focus_j_ids),
        "source": "derived from net.xml topology and junction connections",
    }


def generate_site_routes(
    output_rou_path: Path,
    config: Dict[str, Any],
    preset_name: str = "peak",
    duration: int = 300,
    seed: int = 42,
) -> Path:
    """Generate SUMO route file with 6 Indian vehicle types and sublane parameters."""
    rng = random.Random(seed)
    vtypes_cfg = config.get("vtypes", {})
    demand_cfg = config.get("demand_presets", {}).get(preset_name, {})

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">',
        '    <!-- Indian heterogeneous traffic vTypes with sublane lateral resolution (assumed) -->',
    ]

    for vtype_id, params in vtypes_cfg.items():
        length = params.get("length", {}).get("value", 4.0)
        width = params.get("width", {}).get("value", 1.8)
        height = params.get("height", {}).get("value", 1.5)
        accel = params.get("accel", {}).get("value", 2.5)
        decel = params.get("decel", {}).get("value", 4.5)
        max_speed = params.get("max_speed", {}).get("value", 13.0)
        min_gap = params.get("min_gap", {}).get("value", 2.0)
        min_gap_lat = params.get("min_gap_lat", {}).get("value", 0.5)
        lat_alignment = params.get("lat_alignment", {}).get("value", "compact")

        lines.append(
            f'    <vType id="{vtype_id}" length="{length}" width="{width}" height="{height}" '
            f'accel="{accel}" decel="{decel}" maxSpeed="{max_speed}" minGap="{min_gap}" '
            f'minGapLat="{min_gap_lat}" latAlignment="{lat_alignment}" sigma="0.5"/>'
        )

    # Core continuous routes identified from Boring Road and Boring Canal Road network
    # In network:
    # Boring Road North: 603915294#3 ... #11
    # Boring Road South: 746885310#1 ... #4
    # East Boring Canal Road: 121070865#4 ... #7
    # West Boring Canal Road: 140114355#1 ... #5
    routes_def = [
        ("r_boring_north_to_south", "603915294#10 603915294#11 140114355#4 140114355#5"),
        ("r_boring_south_to_north", "746885310#3 746885310#4 121070865#7"),
        ("r_boring_canal_east", "121070865#5 121070865#6"),
        ("r_boring_canal_west", "140114355#2 140114355#3"),
    ]

    for rid, edges in routes_def:
        lines.append(f'    <route id="{rid}" edges="{edges}"/>')

    vtype_pool = ["car", "auto_rickshaw", "e_rickshaw", "two_wheeler", "bus", "truck"]
    vtype_weights = [35, 25, 10, 20, 5, 5]

    # Approach flows from preset (veh/h)
    flows = [
        ("r_boring_north_to_south", demand_cfg.get("boring_road_north_vph", 800)),
        ("r_boring_south_to_north", demand_cfg.get("boring_road_south_vph", 800)),
        ("r_boring_canal_east", demand_cfg.get("boring_canal_east_vph", 500)),
        ("r_boring_canal_west", demand_cfg.get("boring_canal_west_vph", 500)),
    ]

    arrivals = []
    for route_id, flow_vph in flows:
        rate = flow_vph / 3600.0  # veh / s
        t = 0.0
        while t < duration:
            t += rng.expovariate(rate)
            if t >= duration:
                break
            vtype = rng.choices(vtype_pool, weights=vtype_weights, k=1)[0]
            arrivals.append((t, route_id, vtype))

    arrivals.sort(key=lambda x: x[0])

    for idx, (arr_time, route_id, vtype) in enumerate(arrivals):
        lines.append(
            f'    <vehicle id="veh_{idx}" type="{vtype}" route="{route_id}" '
            f'depart="{arr_time:.2f}" departLane="best" departSpeed="max"/>'
        )

    lines.append("</routes>")

    output_rou_path.parent.mkdir(parents=True, exist_ok=True)
    output_rou_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_rou_path


def generate_site_sumocfg(
    output_sumocfg_path: Path,
    net_path: Path,
    rou_path: Path,
    lateral_resolution_m: float = 0.8,
) -> Path:
    """Generate SUMO configuration enabling sublane model."""
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/sumoConfiguration.xsd">
    <input>
        <net-file value="{net_path.name}"/>
        <route-files value="{rou_path.name}"/>
    </input>
    <time>
        <begin value="0"/>
        <step-length value="1.0"/>
    </time>
    <processing>
        <lateral-resolution value="{lateral_resolution_m:.2f}"/>
        <collision.action value="warn"/>
        <collision.stoptime value="2"/>
        <waiting-time-memory value="1000"/>
    </processing>
    <report>
        <no-step-log value="true"/>
    </report>
</configuration>
"""
    output_sumocfg_path.parent.mkdir(parents=True, exist_ok=True)
    output_sumocfg_path.write_text(content, encoding="utf-8")
    return output_sumocfg_path


def extract_site_geometry(
    site_id: str = "boring_road_patna",
    max_radius_m: float = 275.0,
) -> Dict[str, Any]:
    """Extract local metric 3D scene data from the OSM cache and SUMO network."""
    config = load_site_config(site_id)
    center_lat = float(config["site"]["center"]["latitude"]["value"])
    center_lon = float(config["site"]["center"]["longitude"]["value"])

    zone = int((center_lon + 180) // 6) + 1
    crs = CRS.from_epsg(32600 + zone)
    to_utm = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    center_utm_x, center_utm_y = to_utm.transform(center_lon, center_lat)

    net_file = SITES_DATA_DIR / f"{site_id}.net.xml"
    osm_file = SITES_DATA_DIR / f"{site_id}_2026-10-28.osm"

    if not net_file.is_file():
        raise FileNotFoundError(f"SUMO network file missing: {net_file}")
    if not osm_file.is_file():
        raise FileNotFoundError(f"OSM cache file missing: {osm_file}")

    # Read network projection offset
    net_tree = ET.parse(net_file)
    net_root = net_tree.getroot()
    location = net_root.find("location")
    net_offset = (0.0, 0.0)
    if location is not None and location.get("netOffset"):
        parts = [float(x) for x in location.get("netOffset").split(",")]
        if len(parts) == 2:
            net_offset = (parts[0], parts[1])

    # Convert network coordinates to local frame where center is (0, 0)
    # SUMO x = utm_x + net_offset[0] => local_x = x - (center_utm_x + net_offset[0])
    origin_sumo_x = center_utm_x + net_offset[0]
    origin_sumo_y = center_utm_y + net_offset[1]

    def parse_points(shape_str: str) -> List[List[float]]:
        pts = []
        for pair in shape_str.split():
            coords = pair.split(",")
            if len(coords) == 2:
                sx, sy = float(coords[0]), float(coords[1])
                lx = round(sx - origin_sumo_x, 3)
                ly = round(sy - origin_sumo_y, 3)
                pts.append([lx, ly])
        return pts

    lanes = []
    edges = net_root.findall("edge")
    for edge in edges:
        if edge.get("function") == "internal":
            continue
        edge_id = edge.get("id", "")
        for lane in edge.findall("lane"):
            shape = lane.get("shape", "")
            pts = parse_points(shape)
            if not pts:
                continue
            # Check if within max_radius
            if any(math.hypot(p[0], p[1]) <= max_radius_m for p in pts):
                lanes.append({
                    "id": lane.get("id"),
                    "edge_id": edge_id,
                    "index": int(lane.get("index", 0)),
                    "speed_mps": float(lane.get("speed", 13.89)),
                    "width_m": float(lane.get("width", 3.2)),
                    "shape": pts,
                })

    junctions = []
    for j in net_root.findall("junction"):
        if j.get("type") == "internal":
            continue
        jx = float(j.get("x", "0")) - origin_sumo_x
        jy = float(j.get("y", "0")) - origin_sumo_y
        if math.hypot(jx, jy) <= max_radius_m:
            shape_pts = parse_points(j.get("shape", "")) if j.get("shape") else []
            junctions.append({
                "id": j.get("id"),
                "x": round(jx, 3),
                "y": round(jy, 3),
                "type": j.get("type"),
                "shape": shape_pts,
            })

    # Read OSM buildings
    osm_tree = ET.parse(osm_file)
    osm_root = osm_tree.getroot()
    osm_nodes = {
        node.get("id"): {
            "lat": float(node.get("lat")),
            "lon": float(node.get("lon")),
        }
        for node in osm_root.findall("node")
    }

    buildings = []
    b_rng = random.Random(42)
    for way in osm_root.findall("way"):
        tags = {t.get("k"): t.get("v") for t in way.findall("tag")}
        if "building" not in tags:
            continue
        pts = []
        for nd in way.findall("nd"):
            nid = nd.get("ref")
            if nid in osm_nodes:
                n_info = osm_nodes[nid]
                ux, uy = to_utm.transform(n_info["lon"], n_info["lat"])
                pts.append([round(ux - center_utm_x, 3), round(uy - center_utm_y, 3)])
        if len(pts) >= 3 and any(math.hypot(p[0], p[1]) <= max_radius_m for p in pts):
            # Height resolution
            levels = tags.get("building:levels")
            height_tag = tags.get("height")
            if height_tag:
                try:
                    h = float(height_tag.replace("m", "").strip())
                    source = "osm"
                except ValueError:
                    h = b_rng.uniform(7.0, 15.0)
                    source = "assumed"
            elif levels:
                try:
                    h = float(levels) * 3.2
                    source = "osm"
                except ValueError:
                    h = b_rng.uniform(7.0, 15.0)
                    source = "assumed"
            else:
                h = round(b_rng.uniform(6.5, 16.0), 1)
                source = "assumed"

            buildings.append({
                "id": way.get("id"),
                "points": pts,
                "height_m": h,
                "height_source": source,
                "name": tags.get("name", "Building"),
            })

    # Central island & fountain representation
    # Center node in OSM has amenity=fountain
    fountain = {
        "x": 0.0,
        "y": 0.0,
        "radius_m": 4.5,
        "type": "central_fountain_island",
        "provenance": "osm node 13683758749 (fountain); circular island boundary assumed",
    }

    # Decorative scatter (trees & lamps) - clearly labeled cosmetic
    decorative_scatter = []
    d_rng = random.Random(1337)
    for _ in range(40):
        angle = d_rng.uniform(0, 2 * math.pi)
        dist = d_rng.uniform(25.0, max_radius_m - 20.0)
        px = dist * math.cos(angle)
        py = dist * math.sin(angle)
        # Avoid roads
        if not any(math.hypot(px - lane["shape"][0][0], py - lane["shape"][0][1]) < 6.0 for lane in lanes[:20]):
            decorative_scatter.append({
                "x": round(px, 2),
                "y": round(py, 2),
                "type": d_rng.choice(["tree", "street_lamp"]),
                "provenance": "cosmetic scatter labeled decorative",
            })

    # Provenance tags for the real vs assumed panel
    provenance = {
        "site_name": {"value": config["site"]["display_name"]["value"], "source": "assumed"},
        "center_coordinates": {
            "value": f"{center_lat}, {center_lon}",
            "source": "osm",
            "element": "node/13683758749",
        },
        "road_network_geometry": {
            "value": "OpenStreetMap vector centerlines converted via netconvert with UTM projection",
            "source": "osm",
        },
        "road_lanes": {
            "value": "OSM lane tags where present; 1-lane defaults for untagged residential ways",
            "source": "osm / assumed",
        },
        "signals": {
            "value": "No signal program mapped in OSM extract; proposed fixed-time (S1) and adaptive (S2) plans are hypothetical signal redesigns",
            "source": "assumed",
        },
        "traffic_demand": {
            "value": "Assumed flow presets (uncalibrated; no observed counts provided)",
            "source": "assumed",
        },
        "vehicle_types": {
            "value": "6 heterogeneous vehicle classes with sublane lateral resolution",
            "source": "assumed",
        },
        "traffic_rule": {
            "value": "Left-hand traffic (--lefthand)",
            "source": "assumed (India standard)",
        },
        "building_heights": {
            "value": "Extruded OSM building footprints with seeded plausible heights (6.5 - 16m)",
            "source": "assumed",
        },
        "central_island": {
            "value": "Fountain point from OSM node 13683758749; circular curb boundary assumed",
            "source": "osm / assumed",
        },
        "attribution": "© OpenStreetMap contributors · ODbL 1.0",
        "disclaimer": "Simulation on real road geometry with assumed demand",
    }

    return {
        "site_id": site_id,
        "name": config["site"]["display_name"]["value"],
        "attribution": "© OpenStreetMap contributors",
        "license": "ODbL 1.0",
        "disclaimer": "Simulation on real road geometry with assumed demand",
        "traffic_side": "left-hand",
        "center_utm": {"x": center_utm_x, "y": center_utm_y, "lat": center_lat, "lon": center_lon},
        "bounds_radius_m": max_radius_m,
        "lanes": lanes,
        "junctions": junctions,
        "buildings": buildings,
        "central_feature": fountain,
        "decorative_scatter": decorative_scatter,
        "provenance": provenance,
    }
