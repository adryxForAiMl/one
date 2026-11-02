/**
 * AeroSim Real-World Satellite GPS Map Integration (Leaflet)
 * - High-resolution Satellite Imagery (Esri World Imagery)
 * - Real-time Drone GPS location tracking with rotating heading icon
 * - Flight breadcrumb polyline
 * - Interactive Waypoint Mission Planning on real-world map
 * - Dynamic location preset synchronization
 */

class RealWorldFlightMap {
  constructor(mapContainerId, onMissionUpload) {
    this.containerId = mapContainerId;
    this.onMissionUpload = onMissionUpload;
    this.map = null;
    this.droneMarker = null;
    this.homeMarker = null;
    this.flightPathPolyline = null;
    this.missionPolyline = null;
    this.waypointMarkers = [];

    // State
    this.droneLat = 28.6129;
    this.droneLon = 77.2295;
    this.droneHeading = 0;
    this.homeLat = 28.6129;
    this.homeLon = 77.2295;
    this.flightTrack = [];
    this.plannedWaypoints = [];
    this.isMissionPlanningMode = false;

    this.init();
  }

  init() {
    if (typeof L === 'undefined') {
      console.error('Leaflet library is not loaded');
      return;
    }

    // Default center at New Delhi India Gate
    this.map = L.map(this.containerId, {
      center: [this.droneLat, this.droneLon],
      zoom: 16,
      zoomControl: false,
      attributionControl: false
    });

    // High-resolution Satellite imagery tile layer
    const satLayer = L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 19 }
    );
    satLayer.addTo(this.map);

    // Zoom control on bottom-right
    L.control.zoom({ position: 'bottomright' }).addTo(this.map);

    // Custom Rotating SVG Drone Icon
    const droneSvgIcon = L.divIcon({
      className: 'drone-map-icon-container',
      html: `
        <div id="map-drone-marker" style="transform: rotate(0deg); transition: transform 0.1s linear; width: 34px; height: 34px; display: flex; align-items: center; justify-content: center;">
          <svg width="34" height="34" viewBox="0 0 34 34" fill="none">
            <circle cx="17" cy="17" r="14" fill="rgba(0, 240, 255, 0.25)" stroke="#00f0ff" stroke-width="1.5"/>
            <polygon points="17,5 24,24 17,20 10,24" fill="#00ff9d" stroke="#00f0ff" stroke-width="1"/>
            <circle cx="17" cy="17" r="3" fill="#ffffff"/>
          </svg>
        </div>
      `,
      iconSize: [34, 34],
      iconAnchor: [17, 17]
    });

    this.droneMarker = L.marker([this.droneLat, this.droneLon], { icon: droneSvgIcon }).addTo(this.map);

    // Home Marker
    const homeIcon = L.divIcon({
      className: 'home-marker-icon',
      html: `
        <div style="background: #ffb703; color: #000; font-weight: bold; font-size: 10px; padding: 2px 5px; border-radius: 4px; border: 1px solid #fff; box-shadow: 0 0 8px rgba(255, 183, 3, 0.8);">
          HOME
        </div>
      `,
      iconSize: [40, 18],
      iconAnchor: [20, 9]
    });
    this.homeMarker = L.marker([this.homeLat, this.homeLon], { icon: homeIcon }).addTo(this.map);

    // Flight Path Track Polyline (Cyan glow)
    this.flightPathPolyline = L.polyline([], {
      color: '#00f0ff',
      weight: 3,
      opacity: 0.85,
      dashArray: '6, 6'
    }).addTo(this.map);

    // Mission Route Polyline (Amber)
    this.missionPolyline = L.polyline([], {
      color: '#ffb703',
      weight: 2.5,
      opacity: 0.9
    }).addTo(this.map);

    // Map Click Handler for placing real-world Waypoints
    this.map.on('click', (e) => {
      if (this.isMissionPlanningMode) {
        this.addWaypoint(e.latlng.lat, e.latlng.lng);
      }
    });
  }

  setOrigin(lat, lon, zoom = 16) {
    this.homeLat = lat;
    this.homeLon = lon;
    this.droneLat = lat;
    this.droneLon = lon;
    this.flightTrack = [];

    if (this.map) {
      this.map.setView([lat, lon], zoom);
      this.homeMarker.setLatLng([lat, lon]);
      this.droneMarker.setLatLng([lat, lon]);
      this.flightPathPolyline.setLatLngs([]);
    }
  }

  updateDroneTelemetry(telem) {
    if (!telem || !telem.gps) return;

    const lat = telem.gps.latitude;
    const lon = telem.gps.longitude;
    const heading = telem.attitude ? telem.attitude.yaw : 0;

    if (!lat || !lon) return;

    this.droneLat = lat;
    this.droneLon = lon;
    this.droneHeading = heading;

    // Update Marker position
    if (this.droneMarker) {
      this.droneMarker.setLatLng([lat, lon]);

      // Rotate drone SVG marker to true heading
      const el = document.getElementById('map-drone-marker');
      if (el) {
        el.style.transform = `rotate(${heading}deg)`;
      }
    }

    // Add point to flight trail (throttle to avoid infinite points)
    if (this.flightTrack.length === 0 || this._shouldRecordPoint(lat, lon)) {
      this.flightTrack.push([lat, lon]);
      if (this.flightTrack.length > 500) {
        this.flightTrack.shift();
      }
      this.flightPathPolyline.setLatLngs(this.flightTrack);
    }
  }

  _shouldRecordPoint(lat, lon) {
    const last = this.flightTrack[this.flightTrack.length - 1];
    const dLat = Math.abs(lat - last[0]);
    const dLon = Math.abs(lon - last[1]);
    return (dLat > 0.00002 || dLon > 0.00002); // ~2 meters
  }

  centerOnDrone() {
    if (this.map) {
      this.map.panTo([this.droneLat, this.droneLon]);
    }
  }

  toggleMissionMode(enable) {
    this.isMissionPlanningMode = (enable !== undefined) ? enable : !this.isMissionPlanningMode;
    const mapEl = document.getElementById(this.containerId);
    if (mapEl) {
      mapEl.style.cursor = this.isMissionPlanningMode ? 'crosshair' : 'grab';
    }
    return this.isMissionPlanningMode;
  }

  addWaypoint(lat, lon, alt = 20.0) {
    const wpNum = this.plannedWaypoints.length + 1;
    const wp = {
      id: wpNum,
      latitude: lat,
      longitude: lon,
      altitude: alt,
      speed: 5.0,
      loiter_time: 2.0,
      action: 'WAYPOINT'
    };

    this.plannedWaypoints.push(wp);

    // Add visual marker
    const wpIcon = L.divIcon({
      className: 'wp-pin',
      html: `
        <div style="background: #00f0ff; color: #000; font-weight: 800; font-size: 11px; width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 2px solid #fff; box-shadow: 0 0 10px #00f0ff;">
          ${wpNum}
        </div>
      `,
      iconSize: [22, 22],
      iconAnchor: [11, 11]
    });

    const marker = L.marker([lat, lon], { icon: wpIcon }).addTo(this.map);
    marker.bindPopup(`<b>Waypoint ${wpNum}</b><br>Alt: ${alt}m AGL<br>Speed: 5 m/s`);
    this.waypointMarkers.push(marker);

    // Update mission polyline
    const lineCoords = this.plannedWaypoints.map(w => [w.latitude, w.longitude]);
    this.missionPolyline.setLatLngs(lineCoords);

    this.updateMissionUI();
  }

  clearMission() {
    this.plannedWaypoints = [];
    this.waypointMarkers.forEach(m => this.map.removeLayer(m));
    this.waypointMarkers = [];
    this.missionPolyline.setLatLngs([]);
    this.updateMissionUI();
  }

  updateMissionUI() {
    const statsEl = document.getElementById('mission-wp-count');
    if (statsEl) {
      statsEl.textContent = `${this.plannedWaypoints.length} Waypoints`;
    }
  }

  uploadMission() {
    if (this.plannedWaypoints.length === 0) {
      alert('Please click on the satellite map to add waypoints first.');
      return;
    }
    if (this.onMissionUpload) {
      this.onMissionUpload(this.plannedWaypoints);
    }
  }
}
