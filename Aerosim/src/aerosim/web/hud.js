/**
 * AeroSim Glass Cockpit Aviation Heads-Up Display (HUD)
 * Canvas 2D instrument rendering:
 * - Artificial Horizon & Pitch Ladder
 * - Roll Arc Pointer
 * - Airspeed Tape (Left) & Altitude Tape (Right)
 * - Vertical Speed Indicator (VSI)
 * - Compass Heading Tape (Top)
 * - Flight Path Marker / Boresight
 */

class AviationHUD {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.width = 0;
    this.height = 0;

    // Telemetry storage
    this.telem = {
      pitch: 0,
      roll: 0,
      yaw: 0,
      speed: 0,
      altitude: 0.15,
      climb_rate: 0,
      flight_mode: 'DISARMED',
      is_armed: false,
      wind_speed: 0,
      wind_dir: 0,
    };

    this.resize();
    window.addEventListener('resize', () => this.resize());
  }

  resize() {
    this.width = this.canvas.parentElement.clientWidth || window.innerWidth;
    this.height = this.canvas.parentElement.clientHeight || window.innerHeight;
    this.canvas.width = this.width;
    this.canvas.height = this.height;
  }

  updateTelemetry(telem) {
    if (!telem) return;
    this.telem.pitch = telem.attitude ? telem.attitude.pitch : 0;
    this.telem.roll = telem.attitude ? telem.attitude.roll : 0;
    this.telem.yaw = telem.attitude ? telem.attitude.yaw : 0;
    this.telem.speed = telem.velocity ? telem.velocity.groundspeed : 0;
    this.telem.altitude = telem.position ? telem.position.altitude_agl : 0.15;
    this.telem.climb_rate = telem.velocity ? telem.velocity.climb_rate : 0;
    this.telem.flight_mode = telem.flight_mode || 'DISARMED';
    this.telem.is_armed = telem.is_armed || false;
    if (telem.wind) {
      this.telem.wind_speed = telem.wind.speed || 0;
      this.telem.wind_dir = telem.wind.direction || 0;
    }
    this.draw();
  }

  draw() {
    const ctx = this.ctx;
    const w = this.width;
    const h = this.height;
    const cx = w / 2;
    const cy = h / 2;

    ctx.clearRect(0, 0, w, h);

    // Save context
    ctx.save();

    // Color definitions
    const hudCyan = '#00f0ff';
    const hudGreen = '#00ff9d';
    const hudAmber = '#ffb703';
    const hudDim = 'rgba(0, 240, 255, 0.4)';

    ctx.strokeStyle = hudCyan;
    ctx.fillStyle = hudCyan;
    ctx.lineWidth = 1.5;
    ctx.font = '11px "Share Tech Mono", monospace';

    // 1. Compass Ribbon (Top)
    this.drawCompass(ctx, cx, 36, this.telem.yaw);

    // 2. Artificial Horizon & Pitch Ladder (Center)
    this.drawArtificialHorizon(ctx, cx, cy, this.telem.pitch, this.telem.roll);

    // 3. Central Aircraft Boresight / Reticle
    this.drawBoresight(ctx, cx, cy);

    // 4. Airspeed Tape (Left)
    this.drawSpeedTape(ctx, cx - 180, cy, this.telem.speed);

    // 5. Altitude Tape & VSI (Right)
    this.drawAltitudeTape(ctx, cx + 180, cy, this.telem.altitude, this.telem.climb_rate);

    // 6. Flight Mode & Armed Status Annunciator
    this.drawStatusBanner(ctx, cx, cy - 140);

    ctx.restore();
  }

  drawBoresight(ctx, cx, cy) {
    ctx.save();
    ctx.strokeStyle = '#00f0ff';
    ctx.lineWidth = 2;

    // Center dot
    ctx.beginPath();
    ctx.arc(cx, cy, 3, 0, Math.PI * 2);
    ctx.fillStyle = '#00f0ff';
    ctx.fill();

    // Wings
    ctx.beginPath();
    ctx.moveTo(cx - 30, cy);
    ctx.lineTo(cx - 10, cy);
    ctx.lineTo(cx - 10, cy + 6);

    ctx.moveTo(cx + 30, cy);
    ctx.lineTo(cx + 10, cy);
    ctx.lineTo(cx + 10, cy + 6);
    ctx.stroke();

    ctx.restore();
  }

  drawArtificialHorizon(ctx, cx, cy, pitch, roll) {
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate((roll * Math.PI) / 180);

    const pitchPixelsPerDeg = 3.6;
    const pitchOffset = -pitch * pitchPixelsPerDeg;

    // Pitch Ladder rungs
    for (let deg = -60; deg <= 60; deg += 10) {
      if (deg === 0) continue; // Horizon line handled separately

      const y = pitchOffset - deg * pitchPixelsPerDeg;
      if (Math.abs(y) > 130) continue; // Clip outside viewport center

      const isPositive = deg > 0;
      const rungWidth = 36;
      ctx.strokeStyle = isPositive ? '#00f0ff' : 'rgba(0, 240, 255, 0.6)';
      ctx.lineWidth = 1.5;

      ctx.beginPath();
      if (isPositive) {
        // Solid rungs for climb
        ctx.moveTo(-rungWidth, y);
        ctx.lineTo(-12, y);
        ctx.lineTo(-12, y + 4);

        ctx.moveTo(rungWidth, y);
        ctx.lineTo(12, y);
        ctx.lineTo(12, y + 4);
      } else {
        // Dashed rungs for descent
        ctx.setLineDash([4, 4]);
        ctx.moveTo(-rungWidth, y);
        ctx.lineTo(-12, y);
        ctx.lineTo(-12, y - 4);

        ctx.moveTo(rungWidth, y);
        ctx.lineTo(12, y);
        ctx.lineTo(12, y - 4);
      }
      ctx.stroke();
      ctx.setLineDash([]);

      // Pitch angle text
      ctx.fillStyle = '#00f0ff';
      ctx.font = '10px "Share Tech Mono", monospace';
      ctx.textAlign = 'right';
      ctx.fillText(Math.abs(deg), -rungWidth - 4, y + 3);
      ctx.textAlign = 'left';
      ctx.fillText(Math.abs(deg), rungWidth + 4, y + 3);
    }

    // Roll Angle Scale Arc
    ctx.restore();
    ctx.save();
    ctx.translate(cx, cy);

    ctx.strokeStyle = 'rgba(0, 240, 255, 0.5)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(0, 0, 120, -Math.PI * 0.75, -Math.PI * 0.25);
    ctx.stroke();

    // Roll Tick marks (0, 10, 20, 30, 45, 60 deg)
    const rollMarks = [-60, -45, -30, -20, -10, 0, 10, 20, 30, 45, 60];
    rollMarks.forEach((angle) => {
      const rad = ((angle - 90) * Math.PI) / 180;
      const r1 = 120;
      const r2 = angle === 0 || Math.abs(angle) === 30 || Math.abs(angle) === 60 ? 130 : 125;
      ctx.beginPath();
      ctx.moveTo(Math.cos(rad) * r1, Math.sin(rad) * r1);
      ctx.lineTo(Math.cos(rad) * r2, Math.sin(rad) * r2);
      ctx.stroke();
    });

    // Roll Pointer Triangle
    const pointerRad = ((-roll - 90) * Math.PI) / 180;
    const px = Math.cos(pointerRad) * 115;
    const py = Math.sin(pointerRad) * 115;
    ctx.fillStyle = '#ffb703';
    ctx.beginPath();
    ctx.arc(px, py, 3, 0, Math.PI * 2);
    ctx.fill();

    ctx.restore();
  }

  drawCompass(ctx, cx, cy, yaw) {
    ctx.save();
    const tapeWidth = 320;
    const tapeHeight = 24;

    // Background bar
    ctx.fillStyle = 'rgba(6, 9, 15, 0.7)';
    ctx.fillRect(cx - tapeWidth / 2, cy - tapeHeight / 2, tapeWidth, tapeHeight);
    ctx.strokeStyle = 'rgba(0, 240, 255, 0.3)';
    ctx.strokeRect(cx - tapeWidth / 2, cy - tapeHeight / 2, tapeWidth, tapeHeight);

    // Center marker
    ctx.fillStyle = '#00f0ff';
    ctx.beginPath();
    ctx.moveTo(cx, cy + 14);
    ctx.lineTo(cx - 5, cy + 22);
    ctx.lineTo(cx + 5, cy + 22);
    ctx.closePath();
    ctx.fill();

    // Numerical heading box
    ctx.fillStyle = '#00f0ff';
    ctx.font = 'bold 12px "Share Tech Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText(`${Math.round(yaw).toString().padStart(3, '0')}°`, cx, cy + 36);

    // Compass Tape marks
    const pixelsPerDeg = 2.4;
    ctx.textAlign = 'center';

    for (let deg = -180; deg <= 540; deg += 5) {
      const diff = deg - yaw;
      const x = cx + diff * pixelsPerDeg;
      if (x < cx - tapeWidth / 2 || x > cx + tapeWidth / 2) continue;

      const normDeg = (deg % 360 + 360) % 360;
      let label = null;
      if (normDeg === 0) label = 'N';
      else if (normDeg === 45) label = 'NE';
      else if (normDeg === 90) label = 'E';
      else if (normDeg === 135) label = 'SE';
      else if (normDeg === 180) label = 'S';
      else if (normDeg === 225) label = 'SW';
      else if (normDeg === 270) label = 'W';
      else if (normDeg === 315) label = 'NW';
      else if (normDeg % 10 === 0) label = Math.round(normDeg / 10).toString();

      if (label) {
        ctx.fillStyle = label === 'N' ? '#ff3366' : '#00f0ff';
        ctx.font = label === 'N' ? 'bold 11px sans-serif' : '10px "Share Tech Mono", monospace';
        ctx.fillText(label, x, cy + 3);

        ctx.strokeStyle = '#00f0ff';
        ctx.beginPath();
        ctx.moveTo(x, cy + 6);
        ctx.lineTo(x, cy + 11);
        ctx.stroke();
      } else {
        ctx.strokeStyle = 'rgba(0, 240, 255, 0.4)';
        ctx.beginPath();
        ctx.moveTo(x, cy + 8);
        ctx.lineTo(x, cy + 11);
        ctx.stroke();
      }
    }

    ctx.restore();
  }

  drawSpeedTape(ctx, x, cy, speed) {
    ctx.save();
    const tapeHeight = 180;
    const tapeWidth = 48;

    // Background tape
    ctx.fillStyle = 'rgba(6, 9, 15, 0.6)';
    ctx.fillRect(x - tapeWidth, cy - tapeHeight / 2, tapeWidth, tapeHeight);
    ctx.strokeStyle = 'rgba(0, 240, 255, 0.3)';
    ctx.strokeRect(x - tapeWidth, cy - tapeHeight / 2, tapeWidth, tapeHeight);

    // Ticks (every 2 m/s)
    const pxPerUnit = 8;
    ctx.textAlign = 'right';
    for (let s = Math.max(0, Math.floor(speed - 12)); s <= speed + 12; s++) {
      const y = cy - (s - speed) * pxPerUnit;
      if (y < cy - tapeHeight / 2 || y > cy + tapeHeight / 2) continue;

      if (s % 5 === 0) {
        ctx.strokeStyle = '#00f0ff';
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x - 10, y);
        ctx.stroke();

        ctx.fillStyle = '#00f0ff';
        ctx.font = '10px "Share Tech Mono", monospace';
        ctx.fillText(s, x - 14, y + 3);
      } else {
        ctx.strokeStyle = 'rgba(0, 240, 255, 0.4)';
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x - 5, y);
        ctx.stroke();
      }
    }

    // Speed Digital Readout Box
    ctx.fillStyle = '#0c131f';
    ctx.fillRect(x - tapeWidth - 8, cy - 12, tapeWidth + 8, 24);
    ctx.strokeStyle = '#00f0ff';
    ctx.lineWidth = 1.5;
    ctx.strokeRect(x - tapeWidth - 8, cy - 12, tapeWidth + 8, 24);

    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 12px "Share Tech Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText(`${speed.toFixed(1)}`, x - tapeWidth / 2 - 4, cy + 4);

    // Units
    ctx.fillStyle = 'rgba(0, 240, 255, 0.7)';
    ctx.font = '8px "Share Tech Mono", monospace';
    ctx.fillText('M/S', x - tapeWidth / 2 - 4, cy - 16);

    ctx.restore();
  }

  drawAltitudeTape(ctx, x, cy, alt, climbRate) {
    ctx.save();
    const tapeHeight = 180;
    const tapeWidth = 54;

    // Background tape
    ctx.fillStyle = 'rgba(6, 9, 15, 0.6)';
    ctx.fillRect(x, cy - tapeHeight / 2, tapeWidth, tapeHeight);
    ctx.strokeStyle = 'rgba(0, 240, 255, 0.3)';
    ctx.strokeRect(x, cy - tapeHeight / 2, tapeWidth, tapeHeight);

    // Ticks (every 2m)
    const pxPerUnit = 7;
    ctx.textAlign = 'left';
    for (let a = Math.max(0, Math.floor(alt - 15)); a <= alt + 15; a++) {
      const y = cy - (a - alt) * pxPerUnit;
      if (y < cy - tapeHeight / 2 || y > cy + tapeHeight / 2) continue;

      if (a % 5 === 0) {
        ctx.strokeStyle = '#00f0ff';
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x + 10, y);
        ctx.stroke();

        ctx.fillStyle = '#00f0ff';
        ctx.font = '10px "Share Tech Mono", monospace';
        ctx.fillText(a, x + 14, y + 3);
      } else {
        ctx.strokeStyle = 'rgba(0, 240, 255, 0.4)';
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x + 5, y);
        ctx.stroke();
      }
    }

    // Altitude Digital Readout Box
    ctx.fillStyle = '#0c131f';
    ctx.fillRect(x, cy - 12, tapeWidth + 10, 24);
    ctx.strokeStyle = '#00f0ff';
    ctx.lineWidth = 1.5;
    ctx.strokeRect(x, cy - 12, tapeWidth + 10, 24);

    ctx.fillStyle = '#00ff9d';
    ctx.font = 'bold 12px "Share Tech Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText(`${alt.toFixed(1)}m`, x + (tapeWidth + 10) / 2, cy + 4);

    // VSI (Vertical Speed Indicator Bar) on outer edge
    const vsiX = x + tapeWidth + 14;
    ctx.strokeStyle = 'rgba(0, 240, 255, 0.3)';
    ctx.beginPath();
    ctx.moveTo(vsiX, cy - 50);
    ctx.lineTo(vsiX, cy + 50);
    ctx.stroke();

    // VSI Bug
    const vsiY = Math.max(cy - 50, Math.min(cy + 50, cy - climbRate * 12));
    ctx.fillStyle = climbRate > 0 ? '#00ff9d' : climbRate < 0 ? '#ffb703' : '#00f0ff';
    ctx.beginPath();
    ctx.moveTo(vsiX, vsiY);
    ctx.lineTo(vsiX + 6, vsiY - 4);
    ctx.lineTo(vsiX + 6, vsiY + 4);
    ctx.closePath();
    ctx.fill();

    ctx.restore();
  }

  drawStatusBanner(ctx, cx, y) {
    ctx.save();
    ctx.textAlign = 'center';

    const mode = this.telem.flight_mode;
    const isArmed = this.telem.is_armed;

    ctx.font = 'bold 11px "Orbitron", sans-serif';
    ctx.fillStyle = isArmed ? '#00ff9d' : '#ff3366';
    ctx.fillText(`MODE: ${mode} [${isArmed ? 'ARMED' : 'SAFE'}]`, cx, y);

    ctx.restore();
  }
}
