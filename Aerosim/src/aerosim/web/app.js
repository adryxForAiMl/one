/**
 * AeroSim Ground Control Station (GCS) & Flight Controller
 * - Real-time WebSocket Telemetry & Control Bridge
 * - Virtual Dual Joysticks (Mode 2: Left Throttle/Yaw, Right Pitch/Roll)
 * - Web Gamepad API Support (USB RC Transmitters, Xbox/PS Controllers)
 * - Keyboard Flight Controls
 * - Web Audio API Brushless Motor Turbine Sound Synthesizer
 * - Real-World Location Presets & MAVLink Hardware Bridge UI
 */

class AeroSimGCS {
  constructor() {
    this.ws = null;
    this.wsUrl = `ws://${window.location.host}/ws/telemetry`;
    this.isConnected = false;
    this.telemetry = null;

    // Subsystems
    this.sim3D = null;
    this.hud = null;
    this.flightMap = null;

    // Pilot Stick Inputs (Mode 2)
    this.sticks = {
      throttle: 0.0, // 0.0 to 1.0
      pitch: 0.0,    // -1.0 to 1.0
      roll: 0.0,     // -1.0 to 1.0
      yaw: 0.0       // -1.0 to 1.0
    };

    // Keyboard state
    this.keys = {};

    // Audio Engine
    this.audioCtx = null;
    this.motorOsc = null;
    this.motorGain = null;
    this.audioEnabled = false;

    // Stick drag tracking
    this.activeDragStick = null;

    this.init();
  }

  init() {
    // 1. Initialize 3D Drone Simulation
    this.sim3D = new Drone3DSimulator('three-canvas');

    // 2. Initialize Aviation HUD
    this.hud = new AviationHUD('hud-canvas');

    // 3. Initialize Real-World Map
    this.flightMap = new RealWorldFlightMap('leaflet-map', (waypoints) => {
      this.sendMissionUpload(waypoints);
    });

    // 4. Setup Controls and Listeners
    this.setupKeyboardControls();
    this.setupVirtualJoysticks();
    this.setupGamepadLoop();
    this.setupUIEventListeners();
    this.setupAudioEngine();

    // 5. Connect WebSocket
    this.connectWebSocket();

    // 6. 50Hz Control Loop to send stick inputs
    setInterval(() => this.sendStickInputs(), 20);
  }

  connectWebSocket() {
    console.log(`Connecting to Telemetry WebSocket: ${this.wsUrl}`);
    this.ws = new WebSocket(this.wsUrl);

    this.ws.onopen = () => {
      this.isConnected = true;
      this.updateConnectionBadge(true);
      console.log('Connected to AeroSim Flight Engine.');
    };

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'telemetry') {
          this.handleTelemetry(msg.data);
        } else if (msg.type === 'hardware_status') {
          this.handleHardwareStatus(msg);
        }
      } catch (e) {
        console.error('Error parsing WS message:', e);
      }
    };

    this.ws.onclose = () => {
      this.isConnected = false;
      this.updateConnectionBadge(false);
      console.log('Telemetry WebSocket disconnected. Reconnecting in 2s...');
      setTimeout(() => this.connectWebSocket(), 2000);
    };

    this.ws.onerror = (err) => {
      console.error('WebSocket Error:', err);
    };
  }

  handleTelemetry(data) {
    this.telemetry = data;

    // Update 3D Model
    if (this.sim3D) {
      this.sim3D.updateTelemetry(data);
    }

    // Update 2D Canvas HUD
    if (this.hud) {
      this.hud.updateTelemetry(data);
    }

    // Update Real-World Map
    if (this.flightMap) {
      this.flightMap.updateDroneTelemetry(data);
    }

    // Update UI Indicators
    this.updateUIElements(data);

    // Update Motor Audio Pitch
    this.updateMotorAudio(data);
  }

  updateUIElements(data) {
    // Mode Badge
    const modeBadge = document.getElementById('mode-badge');
    if (modeBadge) {
      modeBadge.textContent = data.flight_mode;
      modeBadge.className = 'mode-badge ' + (data.is_armed ? 'armed' : '') + (data.flight_mode === 'MISSION' ? ' mission' : '');
    }

    // Arming Button
    const armBtn = document.getElementById('btn-arm-toggle');
    if (armBtn) {
      armBtn.textContent = data.is_armed ? 'DISARM MOTORS' : 'ARM MOTORS';
      armBtn.className = 'action-btn arm ' + (data.is_armed ? 'is-armed' : '');
    }

    // Top Bar Tickers
    this.setElText('val-alt', `${data.position.altitude_agl.toFixed(1)} m`);
    this.setElText('val-speed', `${data.velocity.groundspeed.toFixed(1)} m/s`);
    this.setElText('val-bat', `${data.battery.percentage.toFixed(0)}% (${data.battery.voltage.toFixed(1)}V)`);
    this.setElText('val-sats', `${data.gps.satellites} 3D-FIX`);
    this.setElText('val-city', data.origin.city);

    // Motor Gauges
    if (data.motors) {
      this.updateMotorGauge(1, data.motors.m1_rpm, 12000);
      this.updateMotorGauge(2, data.motors.m2_rpm, 12000);
      this.updateMotorGauge(3, data.motors.m3_rpm, 12000);
      this.updateMotorGauge(4, data.motors.m4_rpm, 12000);
    }

    // Battery & Stats Card
    this.setElText('stat-voltage', `${data.battery.voltage.toFixed(2)} V`);
    this.setElText('stat-current', `${data.battery.current.toFixed(1)} A`);
    this.setElText('stat-consumed', `${data.battery.remaining_mah ? (3500 - data.battery.remaining_mah).toFixed(0) : 0} mAh`);
    this.setElText('stat-flight-time', `${Math.floor(data.flight_time / 60)}:${Math.floor(data.flight_time % 60).toString().padStart(2, '0')}`);
    this.setElText('stat-home-dist', `${data.gps.distance_to_home.toFixed(1)} m`);

    // Hardware Bridge indicator
    const hwStatusBadge = document.getElementById('hw-link-indicator');
    if (hwStatusBadge) {
      if (data.operation_mode === 'HARDWARE' && data.hardware_connected) {
        hwStatusBadge.textContent = `MAVLink REAL DRONE [${data.autopilot_firmware}]`;
        hwStatusBadge.style.color = '#00ff9d';
      } else {
        hwStatusBadge.textContent = 'SIMULATION (Digital Twin)';
        hwStatusBadge.style.color = '#00f0ff';
      }
    }
  }

  updateMotorGauge(motorIdx, rpm, maxRpm) {
    const textEl = document.getElementById(`motor-rpm-${motorIdx}`);
    const barEl = document.getElementById(`motor-bar-${motorIdx}`);
    if (textEl) textEl.textContent = `${rpm} RPM`;
    if (barEl) {
      const pct = Math.min(100, Math.max(0, (rpm / maxRpm) * 100));
      barEl.style.width = `${pct}%`;
    }
  }

  setElText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  }

  updateConnectionBadge(connected) {
    const el = document.getElementById('connection-status-dot');
    if (el) {
      el.style.backgroundColor = connected ? '#00ff9d' : '#ff3366';
      el.style.boxShadow = connected ? '0 0 10px #00ff9d' : '0 0 10px #ff3366';
    }
  }

  // --- Controls & Sticks ---
  setupKeyboardControls() {
    window.addEventListener('keydown', (e) => {
      this.keys[e.key.toLowerCase()] = true;
      this.processKeyboardInputs();

      // Quick flight shortcut keys
      if (e.key === ' ' || e.code === 'Space') {
        this.sendModeCommand('POS_HOLD');
      } else if (e.key.toLowerCase() === 't') {
        this.sendModeCommand('AUTO_TAKEOFF');
      } else if (e.key.toLowerCase() === 'l') {
        this.sendModeCommand('AUTO_LAND');
      } else if (e.key.toLowerCase() === 'h') {
        this.sendModeCommand('RTH');
      }
    });

    window.addEventListener('keyup', (e) => {
      this.keys[e.key.toLowerCase()] = false;
      this.processKeyboardInputs();
    });
  }

  processKeyboardInputs() {
    // Mode 2 Standard mapping:
    // W/S or Arrow Up/Down -> Pitch (Forward/Back)
    // A/D or Arrow Left/Right -> Roll (Left/Right)
    // R / F -> Throttle (Climb/Descend)
    // Q / E -> Yaw (Turn Left/Right)

    let pitch = 0.0;
    let roll = 0.0;
    let yaw = 0.0;
    let throttleDelta = 0.0;

    if (this.keys['w'] || this.keys['arrowup']) pitch += 1.0;
    if (this.keys['s'] || this.keys['arrowdown']) pitch -= 1.0;
    if (this.keys['d'] || this.keys['arrowright']) roll += 1.0;
    if (this.keys['a'] || this.keys['arrowleft']) roll -= 1.0;
    if (this.keys['e']) yaw += 1.0;
    if (this.keys['q']) yaw -= 1.0;

    if (this.keys['r']) throttleDelta += 0.04;
    if (this.keys['f']) throttleDelta -= 0.04;

    this.sticks.pitch = pitch;
    this.sticks.roll = roll;
    this.sticks.yaw = yaw;

    if (throttleDelta !== 0.0) {
      this.sticks.throttle = Math.min(1.0, Math.max(0.0, this.sticks.throttle + throttleDelta));
    }

    this.updateStickVisuals();
  }

  setupVirtualJoysticks() {
    // Left Stick (Throttle & Yaw)
    const leftBase = document.getElementById('stick-left');
    const leftThumb = document.getElementById('thumb-left');
    // Right Stick (Pitch & Roll)
    const rightBase = document.getElementById('stick-right');
    const rightThumb = document.getElementById('thumb-right');

    if (leftBase && leftThumb) {
      this.bindStickEvents(leftBase, leftThumb, 'left');
    }
    if (rightBase && rightThumb) {
      this.bindStickEvents(rightBase, rightThumb, 'right');
    }
  }

  bindStickEvents(baseEl, thumbEl, stickType) {
    const handleMove = (clientX, clientY) => {
      const rect = baseEl.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      const radius = rect.width / 2;

      let dx = clientX - centerX;
      let dy = clientY - centerY;
      const dist = Math.sqrt(dx * dx + dy * dy);

      if (dist > radius) {
        dx = (dx / dist) * radius;
        dy = (dy / dist) * radius;
      }

      thumbEl.style.transform = `translate(${dx}px, ${dy}px)`;

      const normX = dx / radius;
      const normY = -dy / radius; // Invert Y so up is positive

      if (stickType === 'left') {
        this.sticks.yaw = normX;
        // Throttle maps from bottom (0.0) to top (1.0)
        this.sticks.throttle = Math.min(1.0, Math.max(0.0, (normY + 1.0) / 2.0));
      } else {
        this.sticks.roll = normX;
        this.sticks.pitch = normY;
      }
    };

    const handleRelease = () => {
      if (stickType === 'right') {
        // Right stick returns to center
        this.sticks.pitch = 0.0;
        this.sticks.roll = 0.0;
        thumbEl.style.transform = 'translate(0px, 0px)';
      } else {
        // Left stick returns yaw to center, keeps current throttle
        this.sticks.yaw = 0.0;
        const currentY = -((this.sticks.throttle * 2.0) - 1.0) * (baseEl.clientWidth / 2);
        thumbEl.style.transform = `translate(0px, ${currentY}px)`;
      }
    };

    baseEl.addEventListener('pointerdown', (e) => {
      baseEl.setPointerCapture(e.pointerId);
      handleMove(e.clientX, e.clientY);

      const onPointerMove = (ev) => handleMove(ev.clientX, ev.clientY);
      const onPointerUp = (ev) => {
        baseEl.releasePointerCapture(ev.pointerId);
        baseEl.removeEventListener('pointermove', onPointerMove);
        baseEl.removeEventListener('pointerup', onPointerUp);
        handleRelease();
      };

      baseEl.addEventListener('pointermove', onPointerMove);
      baseEl.addEventListener('pointerup', onPointerUp);
    });
  }

  updateStickVisuals() {
    const leftThumb = document.getElementById('thumb-left');
    const rightThumb = document.getElementById('thumb-right');
    const maxR = 40;

    if (leftThumb) {
      const x = this.sticks.yaw * maxR;
      const y = -((this.sticks.throttle * 2.0) - 1.0) * maxR;
      leftThumb.style.transform = `translate(${x}px, ${y}px)`;
    }

    if (rightThumb) {
      const x = this.sticks.roll * maxR;
      const y = -this.sticks.pitch * maxR;
      rightThumb.style.transform = `translate(${x}px, ${y}px)`;
    }
  }

  setupGamepadLoop() {
    // Poll Web Gamepad API for connected RC Transmitters / Xbox / PS controllers
    window.addEventListener('gamepadconnected', (e) => {
      console.log(`Gamepad connected: ${e.gamepad.id}`);
      const gpBadge = document.getElementById('gamepad-indicator');
      if (gpBadge) {
        gpBadge.textContent = `RC CONTROLLER: ${e.gamepad.id.slice(0, 16)}...`;
        gpBadge.style.color = '#00ff9d';
      }
    });

    const pollGamepads = () => {
      const gamepads = navigator.getGamepads ? navigator.getGamepads() : [];
      if (gamepads && gamepads[0]) {
        const gp = gamepads[0];
        // Standard Mode 2 Gamepad Axis mapping
        // Axis 0: Left Stick X (Yaw)
        // Axis 1: Left Stick Y (Throttle inverted)
        // Axis 2: Right Stick X (Roll)
        // Axis 3: Right Stick Y (Pitch inverted)
        if (gp.axes.length >= 4) {
          const rawYaw = gp.axes[0];
          const rawThrottle = -gp.axes[1];
          const rawRoll = gp.axes[2];
          const rawPitch = -gp.axes[3];

          // Apply small deadzone
          const deadzone = 0.05;
          this.sticks.yaw = Math.abs(rawYaw) > deadzone ? rawYaw : 0.0;
          this.sticks.throttle = Math.min(1.0, Math.max(0.0, (rawThrottle + 1.0) / 2.0));
          this.sticks.roll = Math.abs(rawRoll) > deadzone ? rawRoll : 0.0;
          this.sticks.pitch = Math.abs(rawPitch) > deadzone ? rawPitch : 0.0;

          this.updateStickVisuals();
        }
      }
      requestAnimationFrame(pollGamepads);
    };
    requestAnimationFrame(pollGamepads);
  }

  sendStickInputs() {
    if (!this.isConnected || !this.ws) return;

    this.ws.send(JSON.stringify({
      type: 'sticks',
      throttle: this.sticks.throttle,
      pitch: this.sticks.pitch,
      roll: this.sticks.roll,
      yaw: this.sticks.yaw
    }));
  }

  // --- Flight Commands ---
  sendArmCommand(arm) {
    if (!this.isConnected) return;
    this.ws.send(JSON.stringify({ type: 'arm', arm: arm }));
  }

  sendModeCommand(modeName) {
    if (!this.isConnected) return;
    this.ws.send(JSON.stringify({ type: 'mode', mode: modeName }));
  }

  sendMissionUpload(waypoints) {
    if (!this.isConnected) return;
    this.ws.send(JSON.stringify({
      type: 'mission_upload',
      waypoints: waypoints
    }));
    alert(`Mission with ${waypoints.length} waypoints uploaded successfully to AeroSim Autopilot!`);
  }

  sendMissionAction(action) {
    if (!this.isConnected) return;
    this.ws.send(JSON.stringify({
      type: 'mission_action',
      action: action
    }));
  }

  // --- Audio Synthesis (Brushless Motor Sound) ---
  setupAudioEngine() {
    const audioBtn = document.getElementById('btn-sound-toggle');
    if (audioBtn) {
      audioBtn.addEventListener('click', () => {
        if (!this.audioEnabled) {
          this.initAudio();
          this.audioEnabled = true;
          audioBtn.textContent = '🔊 AUDIO: ON';
          audioBtn.classList.remove('muted');
        } else {
          this.audioEnabled = false;
          if (this.motorGain) this.motorGain.gain.setValueAtTime(0, this.audioCtx.currentTime);
          audioBtn.textContent = '🔇 AUDIO: OFF';
          audioBtn.classList.add('muted');
        }
      });
    }
  }

  initAudio() {
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      this.audioCtx = new AudioContext();

      // Brushless motor high-frequency whining oscillator
      this.motorOsc = this.audioCtx.createOscillator();
      this.motorOsc.type = 'sawtooth';
      this.motorOsc.frequency.setValueAtTime(80, this.audioCtx.currentTime);

      // Low-pass filter for realistic acoustic body dampening
      const filter = this.audioCtx.createBiquadFilter();
      filter.type = 'lowpass';
      filter.frequency.setValueAtTime(1400, this.audioCtx.currentTime);

      this.motorGain = this.audioCtx.createGain();
      this.motorGain.gain.setValueAtTime(0, this.audioCtx.currentTime);

      this.motorOsc.connect(filter);
      filter.connect(this.motorGain);
      this.motorGain.connect(this.audioCtx.destination);

      this.motorOsc.start();
    } catch (e) {
      console.warn('Web Audio API not allowed without user gesture:', e);
    }
  }

  updateMotorAudio(telem) {
    if (!this.audioEnabled || !this.audioCtx || !this.motorOsc || !this.motorGain) return;

    const rpms = telem.motors ? [telem.motors.m1_rpm, telem.motors.m2_rpm, telem.motors.m3_rpm, telem.motors.m4_rpm] : [0, 0, 0, 0];
    const avgRpm = rpms.reduce((a, b) => a + b, 0) / 4;

    if (telem.is_armed && avgRpm > 200) {
      // Frequency maps from 100Hz to 650Hz based on RPM
      const freq = 90 + (avgRpm / 12000) * 550;
      const gain = Math.min(0.22, 0.04 + (avgRpm / 12000) * 0.18);
      this.motorOsc.frequency.setTargetAtTime(freq, this.audioCtx.currentTime, 0.05);
      this.motorGain.gain.setTargetAtTime(gain, this.audioCtx.currentTime, 0.05);
    } else {
      this.motorGain.gain.setTargetAtTime(0, this.audioCtx.currentTime, 0.05);
    }
  }

  // --- UI Event Listeners ---
  setupUIEventListeners() {
    // Master Arm Toggle
    const armBtn = document.getElementById('btn-arm-toggle');
    if (armBtn) {
      armBtn.addEventListener('click', () => {
        const currentlyArmed = this.telemetry ? this.telemetry.is_armed : false;
        this.sendArmCommand(!currentlyArmed);
      });
    }

    // Auto Takeoff
    const takeoffBtn = document.getElementById('btn-takeoff');
    if (takeoffBtn) {
      takeoffBtn.addEventListener('click', () => this.sendModeCommand('AUTO_TAKEOFF'));
    }

    // Auto Land
    const landBtn = document.getElementById('btn-land');
    if (landBtn) {
      landBtn.addEventListener('click', () => this.sendModeCommand('AUTO_LAND'));
    }

    // Return To Home (RTH)
    const rthBtn = document.getElementById('btn-rth');
    if (rthBtn) {
      rthBtn.addEventListener('click', () => this.sendModeCommand('RTH'));
    }

    // Position Hold
    const posHoldBtn = document.getElementById('btn-pos-hold');
    if (posHoldBtn) {
      posHoldBtn.addEventListener('click', () => this.sendModeCommand('POS_HOLD'));
    }

    // Camera Modes
    document.querySelectorAll('.cam-btn').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.cam-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const mode = btn.dataset.cam;
        if (this.sim3D) {
          this.sim3D.setCameraMode(mode);
        }
      });
    });

    // PiP Map expand / collapse toggle
    const mapExpandBtn = document.getElementById('btn-map-expand');
    const mapWindow = document.getElementById('pip-map-window');
    if (mapExpandBtn && mapWindow) {
      mapExpandBtn.addEventListener('click', () => {
        mapWindow.classList.toggle('expanded');
        mapExpandBtn.textContent = mapWindow.classList.contains('expanded') ? 'Collapse' : 'Expand';
        setTimeout(() => {
          if (this.flightMap && this.flightMap.map) {
            this.flightMap.map.invalidateSize();
          }
        }, 320);
      });
    }

    // Center Map on Drone
    const centerBtn = document.getElementById('btn-map-center');
    if (centerBtn) {
      centerBtn.addEventListener('click', () => {
        if (this.flightMap) this.flightMap.centerOnDrone();
      });
    }

    // Mission Planning Mode Toggle
    const planWpBtn = document.getElementById('btn-plan-wp');
    if (planWpBtn) {
      planWpBtn.addEventListener('click', () => {
        const isPlanning = this.flightMap.toggleMissionMode();
        planWpBtn.classList.toggle('active', isPlanning);
        planWpBtn.textContent = isPlanning ? 'Click Map for WPs' : 'Plan Route';
      });
    }

    // Upload Mission
    const uploadBtn = document.getElementById('btn-upload-mission');
    if (uploadBtn) {
      uploadBtn.addEventListener('click', () => {
        if (this.flightMap) this.flightMap.uploadMission();
      });
    }

    // Start Mission
    const startMissionBtn = document.getElementById('btn-start-mission');
    if (startMissionBtn) {
      startMissionBtn.addEventListener('click', () => {
        this.sendMissionAction('start');
      });
    }

    // Clear Mission
    const clearMissionBtn = document.getElementById('btn-clear-mission');
    if (clearMissionBtn) {
      clearMissionBtn.addEventListener('click', () => {
        if (this.flightMap) this.flightMap.clearMission();
        this.sendMissionAction('clear');
      });
    }

    // Location Presets Modal Trigger
    const locModalBtn = document.getElementById('btn-location-modal');
    const locModal = document.getElementById('location-modal');
    const locCloseBtn = document.getElementById('btn-close-location-modal');
    if (locModalBtn && locModal) {
      locModalBtn.addEventListener('click', () => locModal.classList.add('active'));
    }
    if (locCloseBtn && locModal) {
      locCloseBtn.addEventListener('click', () => locModal.classList.remove('active'));
    }

    // Apply Location Preset
    const applyLocBtn = document.getElementById('btn-apply-location');
    if (applyLocBtn) {
      applyLocBtn.addEventListener('click', () => {
        const select = document.getElementById('location-preset-select');
        if (select && select.value) {
          this.ws.send(JSON.stringify({ type: 'location', preset: select.value }));
          locModal.classList.remove('active');
        }
      });
    }

    // Apply Custom GPS Location
    const applyCustomGpsBtn = document.getElementById('btn-apply-custom-gps');
    if (applyCustomGpsBtn) {
      applyCustomGpsBtn.addEventListener('click', () => {
        const lat = parseFloat(document.getElementById('custom-lat').value);
        const lon = parseFloat(document.getElementById('custom-lon').value);
        const alt = parseFloat(document.getElementById('custom-alt').value);
        if (!isNaN(lat) && !isNaN(lon) && !isNaN(alt)) {
          this.ws.send(JSON.stringify({
            type: 'custom_location',
            lat: lat,
            lon: lon,
            alt: alt,
            name: 'Custom GPS Origin'
          }));
          locModal.classList.remove('active');
        } else {
          alert('Please enter valid numeric latitude, longitude, and altitude values.');
        }
      });
    }

    // Hardware Modal Trigger
    const hwModalBtn = document.getElementById('btn-hardware-modal');
    const hwModal = document.getElementById('hardware-modal');
    const hwCloseBtn = document.getElementById('btn-close-hw-modal');
    if (hwModalBtn && hwModal) {
      hwModalBtn.addEventListener('click', () => {
        this.fetchSerialPorts();
        hwModal.classList.add('active');
      });
    }
    if (hwCloseBtn && hwModal) {
      hwCloseBtn.addEventListener('click', () => hwModal.classList.remove('active'));
    }

    // Hardware Connect Button
    const connectHwBtn = document.getElementById('btn-connect-hardware');
    if (connectHwBtn) {
      connectHwBtn.addEventListener('click', () => {
        const portSelect = document.getElementById('hw-port-select');
        const baudSelect = document.getElementById('hw-baud-select');
        const port = portSelect.value;
        const baud = parseInt(baudSelect.value);

        if (port) {
          this.ws.send(JSON.stringify({
            type: 'connect_hardware',
            port: port,
            baud: baud
          }));
          connectHwBtn.textContent = 'Connecting...';
        }
      });
    }

    // Hardware Disconnect Button
    const disconnectHwBtn = document.getElementById('btn-disconnect-hardware');
    if (disconnectHwBtn) {
      disconnectHwBtn.addEventListener('click', () => {
        this.ws.send(JSON.stringify({ type: 'disconnect_hardware' }));
        hwModal.classList.remove('active');
      });
    }
  }

  fetchSerialPorts() {
    fetch('/api/ports')
      .then(res => res.json())
      .then(data => {
        const portSelect = document.getElementById('hw-port-select');
        if (!portSelect) return;
        portSelect.innerHTML = '';

        // Add UDP option by default
        const udpOpt = document.createElement('option');
        udpOpt.value = 'udpin:0.0.0.0:14550';
        udpOpt.textContent = 'UDP Port 14550 (WiFi / SITL / QGroundControl)';
        portSelect.appendChild(udpOpt);

        if (data.ports && data.ports.length > 0) {
          data.ports.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.device;
            opt.textContent = `${p.device} (${p.description})`;
            portSelect.appendChild(opt);
          });
        }
      })
      .catch(err => console.error('Error fetching ports:', err));
  }

  handleHardwareStatus(msg) {
    const hwModal = document.getElementById('hardware-modal');
    const connectHwBtn = document.getElementById('btn-connect-hardware');
    if (connectHwBtn) {
      connectHwBtn.textContent = msg.connected ? 'Connected' : 'Connect';
    }
    if (msg.connected && hwModal) {
      alert(`Successfully connected to Real Drone MAVLink on ${msg.port}!`);
      hwModal.classList.remove('active');
    }
  }
}

// Instantiate on DOM load
window.addEventListener('DOMContentLoaded', () => {
  window.aeroSim = new AeroSimGCS();
});
