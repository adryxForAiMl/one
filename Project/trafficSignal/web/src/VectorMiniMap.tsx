import type { SiteGeometry, VehicleState } from "./types";

type Props = {
  geometry: SiteGeometry | null;
  vehicles: VehicleState[];
};

export function VectorMiniMap({ geometry, vehicles }: Props) {
  if (!geometry) return null;

  const size = 260;
  const radius = geometry.bounds_radius_m || 275;
  const scale = (size * 0.46) / radius;
  const cx = size / 2;
  const cy = size / 2;

  return (
    <section className="mini-map-card" aria-label="Vector mini-map from OpenStreetMap road polylines">
      <div className="mini-map-header">
        <div>
          <span className="section-kicker">VECTOR RADAR</span>
          <h4>{geometry.name}</h4>
        </div>
        <span className="mini-map-badge">OSM VECTOR ONLY</span>
      </div>

      <div className="mini-map-svg-wrap">
        <svg
          className="mini-map-svg"
          viewBox={`0 0 ${size} ${size}`}
          width={size}
          height={size}
          role="img"
          aria-label="Vector overlay of site geometry and live vehicles (no raster tiles)"
        >
          {/* Background and radius bounds */}
          <rect width={size} height={size} fill="#1a1e23" rx="8" />
          <circle cx={cx} cy={cy} r={radius * scale} fill="none" stroke="#2d3748" strokeWidth="1" strokeDasharray="4 4" />
          <circle cx={cx} cy={cy} r={radius * scale * 0.5} fill="none" stroke="#232b36" strokeWidth="1" />

          {/* Road lane polylines */}
          <g fill="none" stroke="#4a5568" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" opacity="0.85">
            {geometry.lanes.map((lane) => {
              if (lane.shape.length < 2) return null;
              const points = lane.shape
                .map(([x, y]) => `${(cx + x * scale).toFixed(1)},${(cy - y * scale).toFixed(1)}`)
                .join(" ");
              return <polyline key={lane.id} points={points} />;
            })}
          </g>

          {/* Central fountain / island feature */}
          <circle cx={cx} cy={cy} r="4.5" fill="#38b2ac" stroke="#e6fffa" strokeWidth="1.5" />

          {/* Active vehicle dots */}
          <g>
            {vehicles.slice(0, 80).map((v) => {
              const vx = cx + v.x_m * scale;
              const vy = cy - v.y_m * scale;
              return (
                <circle
                  key={v.vehicle_id}
                  cx={vx.toFixed(1)}
                  cy={vy.toFixed(1)}
                  r="2.2"
                  fill="#ecc94b"
                  opacity="0.95"
                />
              );
            })}
          </g>

          {/* Compass rose */}
          <g transform={`translate(${size - 24}, 24)`}>
            <circle r="12" fill="#2d3748" opacity="0.7" />
            <text x="0" y="4" textAnchor="middle" fontSize="9" fill="#e2e8f0" fontWeight="bold">N</text>
          </g>
        </svg>
      </div>

      <div className="mini-map-foot">
        <span>© OpenStreetMap contributors · ODbL</span>
        <b>{vehicles.length} vehicles active</b>
      </div>
    </section>
  );
}
