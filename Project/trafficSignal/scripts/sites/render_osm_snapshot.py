"""Render a static, tile-free SVG from a locally cached OSM XML extract."""

from __future__ import annotations

import argparse
import math
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = ROOT / "data/sites/boring_road_patna_2026-10-28.osm"
DEFAULT_OUTPUT = ROOT / "docs/sites/boring_road_patna.svg"
DEFAULT_CONFIG = ROOT / "config/sites/boring_road_patna.yaml"
CANVAS = 760
PIXELS_PER_METER = 1.15


def project(
    lat: float,
    lon: float,
    center_lat: float,
    center_lon: float,
) -> tuple[float, float]:
    x = (lon - center_lon) * 111_320 * math.cos(math.radians(center_lat))
    y = (center_lat - lat) * 111_320
    return CANVAS / 2 + x * PIXELS_PER_METER, CANVAS / 2 + y * PIXELS_PER_METER


def render(source: Path, output: Path, config_path: Path) -> None:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    center_lat = float(config["site"]["center"]["latitude"]["value"])
    center_lon = float(config["site"]["center"]["longitude"]["value"])
    radius_m = float(config["site"]["radius_m"]["value"])
    root = ET.parse(source).getroot()
    nodes = {
        node.get("id"): (float(node.get("lat")), float(node.get("lon")))
        for node in root.findall("node")
    }
    tagged_nodes = {
        node.get("id"): {tag.get("k"): tag.get("v") for tag in node.findall("tag")}
        for node in root.findall("node")
    }

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS}" height="{CANVAS}" viewBox="0 0 {CANVAS} {CANVAS}">',
        "<rect width=\"100%\" height=\"100%\" fill=\"#f7f9fc\"/>",
        "<g fill=\"#dfe9f3\" stroke=\"#9db2c5\" stroke-width=\"1\">",
    ]

    for way in root.findall("way"):
        tags = {tag.get("k"): tag.get("v") for tag in way.findall("tag")}
        if "building" not in tags:
            continue
        refs = [nd.get("ref") for nd in way.findall("nd")]
        points = [
            project(*nodes[ref], center_lat, center_lon)
            for ref in refs
            if ref in nodes
        ]
        if len(points) < 3 or refs[0] != refs[-1]:
            continue
        points_string = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        parts.append(f'<polygon points="{points_string}"/>')
    parts.append("</g>")

    width_by_highway = {
        "trunk": 11,
        "primary": 10,
        "secondary": 9,
        "tertiary": 7,
        "residential": 5,
        "service": 3,
        "footway": 2,
        "path": 2,
    }
    parts.append('<g fill="none" stroke-linecap="round" stroke-linejoin="round">')
    for way in root.findall("way"):
        tags = {tag.get("k"): tag.get("v") for tag in way.findall("tag")}
        highway = tags.get("highway")
        if highway not in width_by_highway:
            continue
        points = [
            project(*nodes[nd.get("ref")], center_lat, center_lon)
            for nd in way.findall("nd")
            if nd.get("ref") in nodes
        ]
        if len(points) < 2:
            continue
        points_string = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        color = "#657e94" if highway in {"trunk", "primary", "secondary", "tertiary"} else "#9aabba"
        parts.append(
            f'<polyline points="{points_string}" stroke="{color}" '
            f'stroke-width="{width_by_highway[highway]}"/>'
        )
    parts.append("</g>")

    center_x = center_y = CANVAS / 2
    radius = radius_m * PIXELS_PER_METER
    parts.extend(
        [
            f'<circle cx="{center_x:.1f}" cy="{center_y:.1f}" r="{radius:.1f}" fill="none" stroke="#5486b5" stroke-width="2" stroke-dasharray="7 6"/>',
            f'<circle cx="{center_x:.1f}" cy="{center_y:.1f}" r="6" fill="#087e8b" stroke="white" stroke-width="2"/>',
            '<text x="390" y="350" font-family="sans-serif" font-size="12" fill="#075a64">OSM fountain node (candidate center)</text>',
        ]
    )

    for node_id, tags in tagged_nodes.items():
        if tags.get("highway") != "traffic_signals":
            continue
        lat, lon = nodes[node_id]
        x, y = project(lat, lon, center_lat, center_lon)
        if 0 <= x <= CANVAS and 0 <= y <= CANVAS:
            parts.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#e58a3a" stroke="white" stroke-width="1.5"/>'
            )

    parts.extend(
        [
            '<rect x="14" y="14" width="270" height="84" rx="8" fill="white" fill-opacity="0.94" stroke="#c6d3df"/>',
            '<text x="28" y="38" font-family="sans-serif" font-size="16" font-weight="700" fill="#24394d">Boring Road area · OSM vectors</text>',
            '<text x="28" y="59" font-family="sans-serif" font-size="12" fill="#52677b">Candidate center; site identity unconfirmed</text>',
            f'<text x="28" y="79" font-family="sans-serif" font-size="12" fill="#52677b">Dashed ring: {radius_m:g} m · orange: mapped traffic signal</text>',
            '<rect x="14" y="705" width="732" height="40" rx="7" fill="white" fill-opacity="0.94" stroke="#c6d3df"/>',
            '<text x="28" y="730" font-family="sans-serif" font-size="12" fill="#52677b">© OpenStreetMap contributors · ODbL 1.0 · no tiles or imagery · vector extract downloaded 2026-10-28</text>',
            "</svg>",
        ]
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    render(args.source, args.output, args.config)


if __name__ == "__main__":
    main()
