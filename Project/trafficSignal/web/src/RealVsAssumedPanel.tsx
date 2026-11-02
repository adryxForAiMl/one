import { X, CheckCircle, HelpCircle, Info } from "lucide-react";
import type { SiteGeometry } from "./types";

type Props = {
  isOpen: boolean;
  onClose: () => void;
  geometry: SiteGeometry | null;
};

export function RealVsAssumedPanel({ isOpen, onClose, geometry }: Props) {
  if (!isOpen) return null;

  const provenanceItems = [
    {
      parameter: "Road Network Geometry",
      tag: "osm",
      value: "Centerline coordinates from OSM ways",
      note: "Exported from OpenStreetMap ODbL vector data and converted via netconvert (EPSG:32645).",
    },
    {
      parameter: "Traffic Rule (Left-Hand)",
      tag: "assumed",
      value: "Left-Hand Traffic (--lefthand)",
      note: "Standard rule for Indian road networks; enforced by converter and renderer.",
    },
    {
      parameter: "Central Island & Fountain",
      tag: "osm",
      value: "OSM Node 13683758749 (amenity=fountain)",
      note: "Center verified from OSM fountain point; circular island curb is assumed.",
    },
    {
      parameter: "Lane Counts",
      tag: "osm / assumed",
      value: "OSM lanes tag where present; 1-lane defaults for untagged residential ways",
      note: "Boring Road ways (603915294, 746885310) tagged with 2 lanes; side roads assumed 1 lane.",
    },
    {
      parameter: "Lane Merge Patch",
      tag: "assumed",
      value: "Versioned connection patch boring_road_patna.con.xml",
      note: "Enables lane 1 to merge into lane 0 at Boring Road 2-to-1 lane reductions.",
    },
    {
      parameter: "Traffic Signals Presence",
      tag: "assumed",
      value: "No signal program mapped in OSM extract",
      note: "Proposed fixed-time (S1) and adaptive (S2) are hypothetical signal redesigns for testing.",
    },
    {
      parameter: "Traffic Demand Volumes",
      tag: "assumed",
      value: "Assumed presets (off-peak, peak, heavy)",
      note: "Uncalibrated against empirical counts; labeled 'Simulation on real road geometry with assumed demand'.",
    },
    {
      parameter: "Vehicle Fleet Parameters",
      tag: "assumed",
      value: "6 Indian vehicle classes (car, auto, e-rickshaw, 2-wheeler, bus, truck)",
      note: "Physical dimensions and driver acceleration parameters are modeling assumptions.",
    },
    {
      parameter: "Sublane Model Lateral Resolution",
      tag: "assumed",
      value: "0.80 m lateral resolution",
      note: "Enables realistic motorcycle and rickshaw lane sharing and filtering behavior in SUMO.",
    },
    {
      parameter: "Building Heights",
      tag: "assumed",
      value: "Extruded footprints with seeded plausible heights (6.5 - 16m)",
      note: "Building boundaries are from OSM footprints; heights without explicit tags are approximate.",
    },
    {
      parameter: "Trees & Street Lamps",
      tag: "assumed",
      value: "Cosmetic decorative scatter",
      note: "Placed strictly for visual depth; labeled cosmetic scatter.",
    },
  ];

  return (
    <div className="provenance-modal-backdrop" onClick={onClose} role="dialog" aria-modal="true" aria-label="Real versus Assumed site data provenance panel">
      <div className="provenance-modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="provenance-modal-header">
          <div>
            <span className="section-kicker">SITE DATA PROVENANCE</span>
            <h3>Real vs Assumed Attributes · {geometry?.name || "Boring Road Chauraha"}</h3>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close provenance modal">
            <X size={18} />
          </button>
        </div>

        <div className="provenance-banner">
          <Info size={18} className="banner-icon" />
          <p>
            <strong>Honest Provenance Rule:</strong> This simulation is conducted on real road geometry
            from OpenStreetMap with assumed traffic demand. Never present these results as calibrated real Patna traffic.
          </p>
        </div>

        <div className="provenance-table-wrap">
          <table className="provenance-table">
            <thead>
              <tr>
                <th>Site Parameter</th>
                <th>Source Tag</th>
                <th>Value / Model Description</th>
                <th>Methodology / Source Notes</th>
              </tr>
            </thead>
            <tbody>
              {provenanceItems.map((item, idx) => (
                <tr key={idx}>
                  <td className="param-cell"><strong>{item.parameter}</strong></td>
                  <td>
                    <span className={`tag-chip tag-${item.tag.replace(/[^a-z]/g, "")}`}>
                      {item.tag === "osm" ? <CheckCircle size={12} /> : <HelpCircle size={12} />}
                      {item.tag.toUpperCase()}
                    </span>
                  </td>
                  <td>{item.value}</td>
                  <td className="note-cell">{item.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="provenance-modal-footer">
          <span>Map data: © OpenStreetMap contributors (ODbL 1.0)</span>
          <button className="button-primary" onClick={onClose}>Close Panel</button>
        </div>
      </div>
    </div>
  );
}
