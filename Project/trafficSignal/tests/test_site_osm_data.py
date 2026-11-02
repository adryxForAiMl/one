import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OSM_CACHE = PROJECT_ROOT / "data/sites/boring_road_patna_2026-10-28.osm"


def test_boring_road_osm_cache_has_candidate_fountain_and_road():
    root = ET.parse(OSM_CACHE).getroot()
    fountain = root.find("node[@id='13683758749']")
    road = root.find("way[@id='603915294']")

    assert fountain is not None
    assert (fountain.get("lat"), fountain.get("lon")) == ("25.6126047", "85.1188289")
    assert {tag.get("k"): tag.get("v") for tag in fountain.findall("tag")}["amenity"] == "fountain"
    assert road is not None
    road_tags = {tag.get("k"): tag.get("v") for tag in road.findall("tag")}
    assert road_tags["name"] == "Boring Road"
    assert road_tags["lanes"] == "2"
    assert road_tags["oneway"] == "yes"


def test_site_snapshot_renders_from_local_osm_cache_only(tmp_path):
    output = tmp_path / "boring-road.svg"
    script = PROJECT_ROOT / "scripts/sites/render_osm_snapshot.py"

    subprocess.run(
        [sys.executable, str(script), "--source", str(OSM_CACHE), "--output", str(output)],
        check=True,
        cwd=PROJECT_ROOT,
    )

    snapshot = ET.parse(output).getroot()
    assert snapshot.tag.endswith("svg")
    text = " ".join(element.text or "" for element in snapshot.iter())
    assert "OSM fountain node (candidate center)" in text
    assert "275 m" in text
    assert "© OpenStreetMap contributors" in text


def test_boring_road_network_connectivity_passes():
    import json
    report_path = PROJECT_ROOT / "docs/sites/boring_road_patna_network_report.json"
    assert report_path.is_file(), "Network validation report must exist"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["connectivity"]["passes"] is True, "Connectivity gate must pass"
    assert len(report["connectivity"]["incoming_lanes_without_movement"]) == 0
    assert report["geometry_alignment"]["maximum_lane_vertex_to_nearest_osm_road_segment_m"] <= 2.5

