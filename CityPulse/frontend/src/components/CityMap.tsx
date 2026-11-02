"use client";

import L from "leaflet";
import { useEffect, useRef } from "react";
import type { ZonePulse } from "@/lib/types";

interface CityMapProps {
  zones: ZonePulse[];
  selectedZone: string;
  onSelectZone: (zoneId: string) => void;
}

const coordinates: Record<string, [number, number]> = {
  "zone-1": [26.4499, 74.6399],
  "zone-2": [26.2389, 73.0243],
  "zone-3": [26.9124, 75.7873],
};

function colorFor(status: ZonePulse["status"]): string {
  if (status === "elevated") return "#ff806f";
  if (status === "watch") return "#ffc66d";
  return "#65d9c0";
}

export default function CityMap({ zones, selectedZone, onSelectZone }: CityMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const markersRef = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const map = L.map(container, { scrollWheelZoom: false, zoomControl: true });
    map.fitBounds(L.latLngBounds(Object.values(coordinates)), { padding: [28, 28], maxZoom: 8 });
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 18,
    }).addTo(map);
    const markerLayer = L.layerGroup().addTo(map);
    mapRef.current = map;
    markersRef.current = markerLayer;

    return () => {
      map.remove();
      mapRef.current = null;
      markersRef.current = null;
    };
  }, []);

  useEffect(() => {
    const markerLayer = markersRef.current;
    if (!markerLayer) return;
    markerLayer.clearLayers();
    for (const zone of zones) {
      const position = coordinates[zone.zone_id];
      if (!position) continue;
      const color = colorFor(zone.status);
      const selected = zone.zone_id === selectedZone;
      L.circleMarker(position, {
        radius: selected ? 14 : 10,
        color,
        fillColor: color,
        fillOpacity: selected ? 0.72 : 0.42,
        weight: selected ? 3 : 1.5,
      })
        .bindTooltip(`<strong>${zone.name}</strong> · ${zone.pulse_score} pulse`)
        .on("click", () => onSelectZone(zone.zone_id))
        .addTo(markerLayer);
    }
  }, [zones, selectedZone, onSelectZone]);

  return (
    <div ref={containerRef} className="city-map" />
  );
}