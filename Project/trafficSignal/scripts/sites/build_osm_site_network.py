"""Build and validate a clipped SUMO network from the local OSM site cache."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import yaml
from pyproj import CRS, Transformer


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/sites/boring_road_patna.yaml"
DEFAULT_SOURCE = ROOT / "data/sites/boring_road_patna_2026-10-28.osm"
DEFAULT_NETWORK = ROOT / "data/sites/boring_road_patna.net.xml"
DEFAULT_REPORT = ROOT / "docs/sites/boring_road_patna_network_report.json"
DEFAULT_MARKDOWN = ROOT / "docs/sites/boring_road_patna_network_report.md"
DEFAULT_OVERLAY = ROOT / "docs/sites/boring_road_patna_network.svg"
DEFAULT_CONNECTIONS = ROOT / "data/sites/boring_road_patna.con.xml"
PIXELS_PER_METER = 1.15
CANVAS = 760


def config_value(config: dict[str, Any], *path: str) -> Any:
    value: Any = config
    for key in path:
        value = value[key]
    return value["value"]


def find_netconvert() -> str:
    candidates = [
        os.environ.get("NETCONVERT_BINARY"),
        shutil.which("netconvert"),
        str(Path(sys.prefix) / "bin/netconvert"),
        str(ROOT.parent.parent / ".venv/bin/netconvert"),
        str(Path(os.environ["SUMO_HOME"]) / "bin/netconvert") if os.environ.get("SUMO_HOME") else None,
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return candidate
    raise FileNotFoundError(
        "netconvert was not found; install SUMO or set NETCONVERT_BINARY to its executable"
    )


def read_osm(path: Path) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    root = ET.parse(path).getroot()
    nodes = {
        node.get("id"): {
            "lat": float(node.get("lat")),
            "lon": float(node.get("lon")),
            "tags": {tag.get("k"): tag.get("v") for tag in node.findall("tag")},
        }
        for node in root.findall("node")
    }
    ways = [
        {
            "id": way.get("id"),
            "nodes": [item.get("ref") for item in way.findall("nd")],
            "tags": {tag.get("k"): tag.get("v") for tag in way.findall("tag")},
        }
        for way in root.findall("way")
    ]
    return nodes, ways


def parse_shape(shape: str) -> list[tuple[float, float]]:
    return [
        (float(x), float(y))
        for point in shape.split()
        if len((parts := point.split(","))) == 2
        for x, y in (parts,)
    ]


def distance_to_segment(
    point: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
) -> float:
    px, py = point
    sx, sy = start
    ex, ey = end
    dx, dy = ex - sx, ey - sy
    length_squared = dx * dx + dy * dy
    if length_squared == 0:
        return math.hypot(px - sx, py - sy)
    fraction = max(0.0, min(1.0, ((px - sx) * dx + (py - sy) * dy) / length_squared))
    return math.hypot(px - (sx + fraction * dx), py - (sy + fraction * dy))


def point_within_circle(
    point: tuple[float, float],
    center: tuple[float, float],
    radius: float,
) -> bool:
    return math.hypot(point[0] - center[0], point[1] - center[1]) <= radius


def osm_way_id(edge_id: str) -> str | None:
    match = re.match(r"-?\d+", edge_id)
    return match.group(0).lstrip("-") if match else None


def build_boundary(
    center_xy: tuple[float, float],
    radius: float,
    inverse: Transformer,
    vertex_count: int = 48,
) -> str:
    coordinates = []
    cx, cy = center_xy
    for index in range(vertex_count):
        angle = 2 * math.pi * index / vertex_count
        lon, lat = inverse.transform(
            cx + radius * math.cos(angle),
            cy + radius * math.sin(angle),
        )
        coordinates.extend((f"{lon:.8f}", f"{lat:.8f}"))
    return ",".join(coordinates)


def point_to_svg(point: tuple[float, float], center: tuple[float, float]) -> tuple[float, float]:
    return (
        CANVAS / 2 + (point[0] - center[0]) * PIXELS_PER_METER,
        CANVAS / 2 - (point[1] - center[1]) * PIXELS_PER_METER,
    )


def generate_overlay(
    output: Path,
    center: tuple[float, float],
    radius: float,
    osm_nodes: dict[str, dict[str, Any]],
    osm_ways: list[dict[str, Any]],
    transformer: Transformer,
    offset: tuple[float, float],
    network_root: ET.Element,
    max_deviation: float,
) -> None:
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS}" height="{CANVAS}" viewBox="0 0 {CANVAS} {CANVAS}">',
        '<rect width="100%" height="100%" fill="#f7f9fc"/>',
        '<g fill="none" stroke="#71879b" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" opacity="0.75">',
    ]
    for way in osm_ways:
        if "highway" not in way["tags"]:
            continue
        points = []
        for node_id in way["nodes"]:
            node = osm_nodes.get(node_id)
            if node is None:
                continue
            x, y = transformer.transform(node["lon"], node["lat"])
            points.append(point_to_svg((x, y), center))
        if len(points) < 2:
            continue
        shape = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        parts.append(f'<polyline points="{shape}"/>')
    parts.append("</g>")

    parts.append(
        '<g fill="none" stroke="#d44f48" stroke-width="1.25" opacity="0.9" '
        'stroke-linecap="round" stroke-linejoin="round">'
    )
    for edge in network_root.findall("edge"):
        if edge.get("function") == "internal":
            continue
        for lane in edge.findall("lane"):
            points = []
            for x, y in parse_shape(lane.get("shape", "")):
                points.append(point_to_svg((x - offset[0], y - offset[1]), center))
            if len(points) < 2:
                continue
            shape = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
            parts.append(f'<polyline points="{shape}"/>')
    parts.extend(
        [
            "</g>",
            f'<circle cx="{CANVAS / 2:.1f}" cy="{CANVAS / 2:.1f}" r="{radius * PIXELS_PER_METER:.1f}" fill="none" stroke="#5486b5" stroke-width="1.5" stroke-dasharray="7 6"/>',
            f'<circle cx="{CANVAS / 2:.1f}" cy="{CANVAS / 2:.1f}" r="5" fill="#087e8b"/>',
            '<rect x="14" y="14" width="370" height="90" rx="8" fill="white" fill-opacity="0.95" stroke="#c6d3df"/>',
            '<text x="28" y="38" font-family="sans-serif" font-size="16" font-weight="700" fill="#24394d">OSM roads + SUMO lane geometry</text>',
            '<text x="28" y="60" font-family="sans-serif" font-size="12" fill="#52677b">Gray: OSM centerlines · red: SUMO lane polylines</text>',
            f'<text x="28" y="81" font-family="sans-serif" font-size="12" fill="#52677b">Maximum vertex-to-road deviation: {max_deviation:.2f} m</text>',
            '<rect x="14" y="705" width="732" height="40" rx="7" fill="white" fill-opacity="0.95" stroke="#c6d3df"/>',
            '<text x="28" y="730" font-family="sans-serif" font-size="12" fill="#52677b">© OpenStreetMap contributors · ODbL 1.0 · vector data only</text>',
            "</svg>",
        ]
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(parts), encoding="utf-8")


def validate(
    source: Path,
    network_path: Path,
    config: dict[str, Any],
    output_report: Path,
    output_markdown: Path,
    output_overlay: Path,
    netconvert_version: str,
    netconvert_warnings: list[str],
    conversion_options: list[str] | None = None,
) -> dict[str, Any]:
    osm_nodes, osm_ways = read_osm(source)
    network_root = ET.parse(network_path).getroot()
    center_lat = float(config_value(config, "site", "center", "latitude"))
    center_lon = float(config_value(config, "site", "center", "longitude"))
    radius = float(config_value(config, "site", "radius_m"))
    zone = int((center_lon + 180) // 6) + 1
    crs = CRS.from_epsg(32600 + zone)
    to_utm = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    from_utm = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    center = to_utm.transform(center_lon, center_lat)
    location = network_root.find("location")
    if location is None or not location.get("netOffset"):
        raise ValueError("Generated SUMO network is missing its projection offset")
    offset = tuple(float(value) for value in location.get("netOffset").split(","))
    if len(offset) != 2:
        raise ValueError(f"Unexpected SUMO net offset: {location.get('netOffset')}")
    net_center = (center[0] + offset[0], center[1] + offset[1])

    way_tags = {way["id"]: way["tags"] for way in osm_ways}
    road_segments: list[tuple[tuple[float, float], tuple[float, float]]] = []
    for way in osm_ways:
        if "highway" not in way["tags"]:
            continue
        points = []
        for node_id in way["nodes"]:
            node = osm_nodes.get(node_id)
            if node is None:
                continue
            x, y = to_utm.transform(node["lon"], node["lat"])
            points.append((x + offset[0], y + offset[1]))
        road_segments.extend(zip(points, points[1:]))
    if not road_segments:
        raise ValueError("OSM extract contains no highway geometry for alignment validation")

    deviations = []
    lane_point_count = 0
    for edge in network_root.findall("edge"):
        if edge.get("function") == "internal":
            continue
        for lane in edge.findall("lane"):
            for point in parse_shape(lane.get("shape", "")):
                if point_within_circle(point, net_center, radius + 1):
                    lane_point_count += 1
                    deviations.append(
                        min(distance_to_segment(point, start, end) for start, end in road_segments)
                    )
    if not deviations:
        raise ValueError("No SUMO lane shape vertices found inside the configured site radius")
    deviations.sort()
    max_deviation = deviations[-1]
    p95_index = min(len(deviations) - 1, math.ceil(len(deviations) * 0.95) - 1)

    junctions = []
    for junction in network_root.findall("junction"):
        if junction.get("type") == "internal":
            continue
        point = (float(junction.get("x")), float(junction.get("y")))
        d = math.hypot(point[0] - net_center[0], point[1] - net_center[1])
        junctions.append((d, junction))
    junctions.sort(key=lambda item: item[0])
    if not junctions:
        raise ValueError("SUMO network contains no external junctions")
    nearest_distance, nearest_junction = junctions[0]
    focus_junctions = [
        (distance, junction)
        for distance, junction in junctions
        if distance <= 50.0
    ]
    checked_junctions = [
        (distance, junction)
        for distance, junction in junctions
        if distance < radius - 12.0
        and junction.get("type") not in {"dead_end", "unregulated"}
    ]

    edges = {
        edge.get("id"): edge
        for edge in network_root.findall("edge")
        if edge.get("function") != "internal"
    }
    outgoing_by_node: dict[str, list[str]] = {}
    incoming_by_node: dict[str, list[str]] = {}
    for edge in edges.values():
        outgoing_by_node.setdefault(edge.get("from", ""), []).append(edge.get("id", ""))
        incoming_by_node.setdefault(edge.get("to", ""), []).append(edge.get("id", ""))
    connections = network_root.findall("connection")
    connections_by_lane: dict[tuple[str, str], list[ET.Element]] = {}
    for connection in connections:
        key = (connection.get("from", ""), connection.get("fromLane", ""))
        connections_by_lane.setdefault(key, []).append(connection)

    missing_movements = []
    checked_lanes = 0
    for _, junction in checked_junctions:
        junction_id = junction.get("id", "")
        if not outgoing_by_node.get(junction_id):
            continue
        for edge_id in incoming_by_node.get(junction_id, []):
            edge = edges[edge_id]
            for lane_index, _lane in enumerate(edge.findall("lane")):
                checked_lanes += 1
                if not connections_by_lane.get((edge_id, str(lane_index))):
                    missing_movements.append(
                        {"junction": junction_id, "edge": edge_id, "lane": lane_index}
                    )

    lane_counts = []
    movement_records = []
    focus_ids = {junction.get("id") for _, junction in focus_junctions}
    focus_incoming = {
        edge_id
        for junction_id in focus_ids
        for edge_id in incoming_by_node.get(junction_id, [])
    }
    for edge_id in sorted(focus_incoming):
        edge = edges[edge_id]
        way_id = osm_way_id(edge_id)
        tags = way_tags.get(way_id or "", {})
        lane_count_text = tags.get("lanes")
        lane_counts.append(
            {
                "junction_id": edge.get("to"),
                "edge_id": edge_id,
                "osm_way_id": way_id,
                "road_name": tags.get("name"),
                "sumo_lanes": len(edge.findall("lane")),
                "osm_lanes": int(lane_count_text) if lane_count_text and lane_count_text.isdigit() else None,
                "lane_count_source": "osm" if lane_count_text and lane_count_text.isdigit() else "assumed",
                "oneway": tags.get("oneway"),
                "highway": tags.get("highway"),
            }
        )
    for connection in connections:
        if connection.get("from") in focus_incoming:
            movement_records.append(
                {
                    "junction_id": edges[connection.get("from", "")].get("to"),
                    "from_edge": connection.get("from"),
                    "from_lane": int(connection.get("fromLane", "0")),
                    "to_edge": connection.get("to"),
                    "to_lane": int(connection.get("toLane", "0")),
                    "direction": connection.get("dir"),
                    "signal_id": connection.get("tl"),
                    "signal_link_index": connection.get("linkIndex"),
                }
            )

    tagged_roundabouts = []
    for way in osm_ways:
        if way["tags"].get("junction") != "roundabout":
            continue
        for node_id in way["nodes"]:
            node = osm_nodes.get(node_id)
            if node is None:
                continue
            x, y = to_utm.transform(node["lon"], node["lat"])
            if math.hypot(x - center[0], y - center[1]) <= radius:
                tagged_roundabouts.append(way["id"])
                break
    tagged_signals = []
    for node_id, node in osm_nodes.items():
        if node["tags"].get("highway") != "traffic_signals":
            continue
        x, y = to_utm.transform(node["lon"], node["lat"])
        d = math.hypot(x - center[0], y - center[1])
        if d <= radius:
            tagged_signals.append({"node_id": node_id, "distance_m": round(d, 1)})

    osm_classification = (
        "roundabout"
        if tagged_roundabouts
        else "signalized"
        if tagged_signals
        else "unclassified in OSM; missing tags do not establish real-world control"
    )
    lane_width_sources = {"osm": 0, "assumed": 0}
    for edge in network_root.findall("edge"):
        if edge.get("function") == "internal":
            continue
        tags = way_tags.get(osm_way_id(edge.get("id", "")) or "", {})
        provenance = "osm" if tags.get("width") else "assumed"
        lane_width_sources[provenance] += len(edge.findall("lane"))

    report: dict[str, Any] = {
        "site_id": config_value(config, "site", "id"),
        "source_file": source.relative_to(ROOT).as_posix() if source.is_relative_to(ROOT) else source.name,
        "network_file": network_path.relative_to(ROOT).as_posix() if network_path.is_relative_to(ROOT) else network_path.name,
        "osm_download_date": config_value(config, "map", "downloaded"),
        "attribution": config_value(config, "map", "attribution"),
        "center": {"latitude": center_lat, "longitude": center_lon},
        "radius_m": radius,
        "projection": crs.to_string(),
        "netconvert_version": netconvert_version.strip(),
        "conversion_options": conversion_options or [
            "--lefthand",
            "--roundabouts.guess",
            "--junctions.join",
            "--junctions.join-dist 10",
            "--proj.utm",
            "--keep-edges.in-geo-boundary <48-vertex 275 m circle>",
        ],
        "netconvert_warnings": netconvert_warnings,
        "osm_control_evidence": {
            "classification": osm_classification,
            "roundabout_way_ids": tagged_roundabouts,
            "signal_nodes_within_radius": tagged_signals,
            "center_feature": "amenity=fountain at OSM node 13683758749",
            "island_boundary": "not mapped by the fountain point; unknown",
        },
        "sumo_nearest_junction": {
            "id": nearest_junction.get("id"),
            "type": nearest_junction.get("type"),
            "distance_from_candidate_center_m": round(nearest_distance, 2),
            "component_junctions_within_50m": [
                {
                    "id": junction.get("id"),
                    "type": junction.get("type"),
                    "distance_m": round(distance, 2),
                    "incoming_lanes": len(junction.get("incLanes", "").split()),
                }
                for distance, junction in focus_junctions
            ],
        },
        "approach_lanes": lane_counts,
        "allowed_movements_from_netconvert": movement_records,
        "connectivity": {
            "junctions_checked": len(checked_junctions),
            "incoming_lanes_checked": checked_lanes,
            "incoming_lanes_without_movement": missing_movements,
            "passes": not missing_movements and checked_lanes > 0,
            "method": "Each imported incoming lane at an internal junction in the site radius must have at least one generated SUMO connection.",
        },
        "geometry_alignment": {
            "lane_shape_vertices_checked": lane_point_count,
            "maximum_lane_vertex_to_nearest_osm_road_segment_m": round(max_deviation, 3),
            "p95_lane_vertex_to_nearest_osm_road_segment_m": round(deviations[p95_index], 3),
            "comparison": "SUMO lane shape vertices to closest OSM highway centerline segment in UTM meters; this is a geometric discrepancy measure, not ground-truth accuracy.",
            "lane_width_tag_counts": lane_width_sources,
            "width_provenance_note": "SUMO width defaults are not treated as surveyed widths; widths without explicit OSM tags remain assumed.",
        },
    }
    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown_report(report, output_markdown)
    generate_overlay(
        output_overlay,
        center,
        radius,
        osm_nodes,
        osm_ways,
        to_utm,
        offset,
        network_root,
        max_deviation,
    )
    return report


def write_markdown_report(report: dict[str, Any], output: Path) -> None:
    evidence = report["osm_control_evidence"]
    nearest = report["sumo_nearest_junction"]
    connectivity = report["connectivity"]
    alignment = report["geometry_alignment"]
    lines = [
        "# Boring Road candidate — SUMO network validation",
        "",
        f"**OSM attribution:** {report['attribution']} · ODbL 1.0",
        "",
        "The site identity is provisional. No signal program or central-island footprint is inferred from missing OSM tags.",
        "",
        "## Build and control evidence",
        "",
        f"- Raw OSM cache: `{report['source_file']}` (downloaded {report['osm_download_date']}).",
        f"- SUMO network: `{report['network_file']}`.",
        f"- Converter: `{report['netconvert_version']}`.",
        f"- UTM frame: {report['projection']}; center {report['center']['latitude']}, {report['center']['longitude']}; radius {report['radius_m']} m.",
        f"- Options: `{', '.join(report['conversion_options'])}`.",
        f"- OSM control classification: {evidence['classification']}. Roundabout ways: {evidence['roundabout_way_ids'] or 'none tagged in radius'}. Signal nodes in radius: {evidence['signal_nodes_within_radius'] or 'none tagged in radius'}.",
        f"- Nearest generated SUMO junction: `{nearest['id']}` (`{nearest['type']}`), {nearest['distance_from_candidate_center_m']} m from the candidate center. The 50 m focus area contains {len(nearest['component_junctions_within_50m'])} separate generated junction nodes; these are not silently merged into a fabricated single junction.",
        "",
        "## Approach lanes",
        "",
        "| SUMO junction | Incoming edge | OSM way/name | SUMO lanes | OSM lane tag | Lane-count provenance |",
        "|---|---|---|---:|---:|---|",
    ]
    for approach in report["approach_lanes"]:
        name = approach["road_name"] or "(unnamed)"
        lanes = approach["osm_lanes"] if approach["osm_lanes"] is not None else "not tagged"
        lines.append(
            f"| `{approach['junction_id']}` | `{approach['edge_id']}` | `{approach['osm_way_id']}` {name} | {approach['sumo_lanes']} | {lanes} | `{approach['lane_count_source']}` |"
        )
    lines.extend(
        [
            "",
            "SUMO lane counts shown where OSM has no `lanes` tag are imported defaults, not measured lane counts.",
            "",
            "## Connectivity and geometry alignment",
            "",
            f"- Connectivity: **{'PASS' if connectivity['passes'] else 'FAIL'}** — {connectivity['incoming_lanes_checked']} incoming lanes checked at {connectivity['junctions_checked']} internal junctions; {len(connectivity['incoming_lanes_without_movement'])} have no generated movement.",
            f"- Lane vertices compared: {alignment['lane_shape_vertices_checked']}. Maximum deviation: **{alignment['maximum_lane_vertex_to_nearest_osm_road_segment_m']} m**; p95: {alignment['p95_lane_vertex_to_nearest_osm_road_segment_m']} m.",
            f"- Deviation compares SUMO lane polylines to OSM road centerline segments in UTM coordinates. It is not a survey-accuracy claim. See [`boring_road_patna_network.svg`](boring_road_patna_network.svg) for the vector overlay.",
            "",
            "## Warnings",
            "",
        ]
    )
    lines.extend(f"- {warning}" for warning in report["netconvert_warnings"])
    if not report["netconvert_warnings"]:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "No junction signal timings are included in this generated geometry report. OSM records a fountain point, not an island boundary or signal program.",
        ]
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--network", type=Path, default=DEFAULT_NETWORK)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--overlay", type=Path, default=DEFAULT_OVERLAY)
    parser.add_argument("--connections", type=Path, default=DEFAULT_CONNECTIONS)
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    center_lat = float(config_value(config, "site", "center", "latitude"))
    center_lon = float(config_value(config, "site", "center", "longitude"))
    radius = float(config_value(config, "site", "radius_m"))
    zone = int((center_lon + 180) // 6) + 1
    crs = CRS.from_epsg(32600 + zone)
    forward = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    inverse = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    center_xy = forward.transform(center_lon, center_lat)
    args.network.parent.mkdir(parents=True, exist_ok=True)
    netconvert = find_netconvert()
    version = subprocess.run(
        [netconvert, "--version"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()[0]
    boundary = build_boundary(center_xy, radius, inverse)
    conversion_opts = [
        "--lefthand",
        "--roundabouts.guess",
        "--junctions.join",
        "--junctions.join-dist",
        "10",
        "--proj.utm",
        "--keep-edges.in-geo-boundary",
        boundary,
    ]
    report_opts = [
        "--lefthand",
        "--roundabouts.guess",
        "--junctions.join",
        "--junctions.join-dist 10",
        "--proj.utm",
        "--keep-edges.in-geo-boundary <48-vertex 275 m circle>",
    ]
    if args.connections and args.connections.exists():
        conversion_opts.extend(["--connection-files", str(args.connections.resolve())])
        report_opts.append(f"--connection-files {args.connections.name} (assumed merge patch for Boring Road lane drops)")
    command = [
        netconvert,
        "--osm-files",
        str(args.source.resolve()),
        *conversion_opts,
        "--output-file",
        str(args.network.resolve()),
    ]
    conversion = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if conversion.stdout:
        print(conversion.stdout, end="")
    if conversion.stderr:
        print(conversion.stderr, file=sys.stderr, end="")
    warnings = [
        line.strip()
        for line in (conversion.stdout + "\n" + conversion.stderr).splitlines()
        if "Warning:" in line
    ]
    report = validate(
        args.source.resolve(),
        args.network.resolve(),
        config,
        args.report,
        args.markdown,
        args.overlay,
        version,
        warnings,
        conversion_options=report_opts,
    )
    print(f"Network: {args.network}")
    print(f"Validation report: {args.report}")
    print(f"Geometry overlay: {args.overlay}")
    print(
        f"Connectivity {'passed' if report['connectivity']['passes'] else 'failed'}; "
        f"maximum lane-to-OSM deviation "
        f"{report['geometry_alignment']['maximum_lane_vertex_to_nearest_osm_road_segment_m']:.3f} m"
    )
    if not report["connectivity"]["passes"]:
        raise SystemExit("Connectivity validation failed; inspect the generated report before use.")


if __name__ == "__main__":
    main()
