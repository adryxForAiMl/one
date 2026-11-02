# 🛸 AeroSim - Advanced Drone Flight Simulator & Ground Control Station (GCS)

AeroSim ek complete, modern **Python Backend** aur **Photorealistic 3D Web Frontend** drone simulator aur Ground Control Station hai. Isme original, realistic quadcopter drone model, accurate 6-DOF physics, aviation-grade HUD, real-world satellite GPS map tracking, aur **Real Physical Drone ko MAVLink (Serial / UDP) ke through real world me udane** ka complete support shamil hai.

---

## 🌟 Key Features (Mukhya Khasiyat)

### 1. 🛩️ Authentic 3D Drone Model ("Original 3D Drone")
- **High-Fidelity 3D Quadcopter**: Sleek carbon-fiber composite body, top aerodynamic canopy, internal battery bay, front stereo obstacle-avoidance dual optical lenses.
- **Realistic Brushless Motors & Propellers**:
  - High-torque brushless outrunners with visible copper coils and CNC aluminum bells.
  - Aerodynamic curved twin-blade propellers.
  - **Dynamic High-RPM Motion Blur Discs**: High speed par propellers realistic semi-transparent aerodynamic blur disc aur tip vortices me convert hote hain.
- **3-Axis Stabilized Gimbal 4K Camera**: Nose par mounted gimbal jo real-time pitch tilt follow karta hai (Chase view aur First-Person FPV Cockpit view ke saath).
- **Aviation Navigation Strobe LEDs**:
  - Front Right: Aviation Green LED
  - Front Left: Aviation Red LED
  - Rear: Pulsing White Strobe Beacons
  - Canopy: Flight status beacon (Disarmed par pulsing amber/red, Armed par pulsing green, Mission par cyan).
- **Prop-Wash Dust Ground Effect**: Jab drone zameen ke kareeb hover karta hai, realistic dust particles ground par swirl karte hain.

### 2. 🌍 Real-World Flight & GPS Navigation ("Real World me Udana")
- **WGS-84 Global GPS Coordinates**: Local Cartesian NED coordinates real-time me accurate Latitude, Longitude aur Altitude MSL me convert hote hain.
- **Real-World Global Presets**:
  - 🇮🇳 **New Delhi**: India Gate & Kartavya Path (28.6129° N, 77.2295° E, Alt 215m)
  - 🇮🇳 **Mumbai**: Marine Drive & Gateway of India (18.9220° N, 72.8347° E, Alt 14m)
  - 🇮🇳 **Bengaluru**: Electronic City Drone Corridor (12.8452° N, 77.6602° E, Alt 900m)
  - 🇺🇸 **San Francisco**: Golden Gate Strait & Bay (37.8024° N, -122.4646° E, Alt 15m)
  - 🇦🇪 **Dubai**: Dubai Marina & Coastal Airspace (25.0772° N, 55.1330° E, Alt 8m)
  - 🇨🇭 **Swiss Alps**: Interlaken Alpine Valley (46.6863° N, 7.8632° E, Alt 566m)
  - 🇯🇵 **Tokyo**: Tokyo Bay & Odaiba (35.6264° N, 139.7744° E, Alt 6m)
  - 📍 **Custom Coordinates**: Duniya ke kisi bhi kone ka Latitude, Longitude aur Altitude daal kar drone wahan deploy kar sakte hain!
- **Interactive Satellite GPS Map (Leaflet)**:
  - High-resolution Esri World Satellite imagery layer.
  - Real-time rotating drone marker jo drone ke actual compass heading ke sath spin karta hai.
  - Live breadcrumb flight path trail.
  - Home launch point marker for Return-To-Home (RTH).
- **Autonomous Waypoint Mission Planner**:
  - Satellite map par click karke waypoints drop karein (WP 1, WP 2, WP 3...).
  - Click "Upload Mission" aur "Fly Mission" — drone automatically takeoff karega, real-world waypoints traverse karega aur safely return ya land karega!

### 3. ⚡ Real Drone Hardware Bridge (MAVLink / Pixhawk / ArduPilot / PX4)
- **Real Physical Drone Connection**:
  - Agar aapke paas real physical drone hai (Pixhawk, ArduPilot, PX4, ya ESP32 drone), toh aap use USB Serial port (jaise `/dev/cu.usbserial*` ya Telemetry Radio 57600/115200 baud) ya WiFi UDP port `14550` par connect kar sakte hain.
  - AeroSim real drone se live telemetry receive karta hai aur use real commands (Arm, Takeoff, Land, RTL, RC Override) bhej sakta hai!
- **Digital Twin Simulation Mode**:
  - Jab physical drone connected nahi hota, AeroSim ka internal high-precision 6-DOF non-linear physics engine aur PID autopilot execute hota hai.

### 4. 🎛️ Aviation Glass Cockpit HUD & Telemetry
- **Artificial Horizon & Pitch Ladder**: -90° se +90° pitch rungs aur roll angle scale pointer.
- **Airspeed & Altitude Tapes**: Left side groundspeed tape aur Right side altitude tape vertical speed indicator (VSI m/s) ke sath.
- **Top 360° Compass Ribbon**: Cardinal directions (N, NE, E, SE, S, SW, W, NW) aur Home direction diamond pointer.
- **Motor Gauges**: M1, M2, M3, M4 RPM aur thrust bars.
- **LiPo Battery Health**: 4S pack voltage, current draw (Amps), consumed capacity (mAh), aur remaining percentage.
- **Audio Turbine Synthesizer**: Web Audio API oscillator jo brushless motors ke exact RPM ke hisaab se realistic acoustic turbine whine generate karta hai.

---

## 🚀 Quick Start (Kaise Chalayein)

### 1. Requirements Install Karein
```bash
cd /Users/adityakumar/Documents/VSCODE/Aerosim
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. AeroSim GCS aur 3D Simulator Start Karein
Aap do tareeqon se launch kar sakte hain:

**Option A: Python Module se**
```bash
python3 -m aerosim.main
```

**Option B: Direct Run Script se**
```bash
python3 scripts/run.py
```

Server start ho kar automatically aapke browser me `http://127.0.0.1:8000` open kar dega!

---

## 🎮 Flight Controls (Drone Kaise Udayein)

### 🕹️ Keyboard Controls (Mode 2)
| Key | Action |
|---|---|
| `W` / `Arrow Up` | Pitch Forward (Aage badhein) |
| `S` / `Arrow Down` | Pitch Backward (Peeche aayein) |
| `A` / `Arrow Left` | Roll Left (Baayein jhukein) |
| `D` / `Arrow Right` | Roll Right (Daayein jhukein) |
| `R` | Throttle Up (Climb / Oopar uthein) |
| `F` | Throttle Down (Descend / Neeche aayein) |
| `Q` | Yaw Left (Baayein ghoomein) |
| `E` | Yaw Right (Daayein ghoomein) |
| `T` | **Auto Takeoff** (Automatic 8m tak climb) |
| `L` | **Auto Land** (Gentle smooth landing) |
| `H` | **Return To Home (RTH)** (Launch point par wapas aana) |
| `Space` | **Position Hold / Loiter** (Hover in place) |

### 📱 Virtual Dual Touch/Mouse Joysticks
- **Left Stick**: Throttle (Vertical) & Yaw (Horizontal)
- **Right Stick**: Pitch (Vertical) & Roll (Horizontal)
- Return-to-center spring action ke sath tablet/touch aur mouse dono support karta hai.

### 🎮 USB RC Transmitter & Gamepad Support
- Koi bhi USB RC Transmitter (Radiomaster, FrSky, FlySky) ya Xbox/PlayStation controller computer se connect karein. Web Gamepad API automatically detect karke smooth analog stick inputs enable kar deta hai.

---

## 🗺️ Real World Waypoint Mission Kaise Banayein

1. Screen par right side me **Satellite GPS Map** dekhein.
2. **"Plan Route"** button par click karein.
3. Satellite map par zameen par alag-alag jagahon par click karke waypoints add karein (WP 1, WP 2, WP 3...).
4. **"Upload"** button dabayein — waypoints AeroSim ke autopilot me upload ho jayenge.
5. **"Fly Mission"** button dabayein — drone takeoff karega, har waypoint ko sequential speed aur altitude par fly karega, aur end par hold ya RTH karega!

---

## 📡 Real Physical Drone Connect Karna (MAVLink Hardware)

1. Top bar me **"⚡ Connect Real Drone"** button click karein.
2. Select karein:
   - **Serial Port**: Drone ka USB port (jaise `/dev/cu.usbserial-xxx`) aur baud rate (e.g. `115200` ya `57600`).
   - **UDP Network**: Agar drone WiFi/Telemetry relay par hai, toh `udpin:0.0.0.0:14550` select karein.
3. Click **"Connect to Real Drone"**.
4. Drone ka live IMU attitude, real GPS location, battery aur status AeroSim 3D HUD aur satellite map par stream hona shuru ho jayega!

---

## 📂 Code Architecture

```
Aerosim/
├── requirements.txt              # Backend & MAVLink dependencies
├── pyproject.toml                # Project configuration
├── scripts/
│   └── run.py                    # One-click execution launcher
└── src/
    └── aerosim/
        ├── main.py               # Unified CLI & server launcher
        ├── server.py             # FastAPI WebSocket (50Hz) & REST API server
        ├── simulation/
        │   └── unified_flight_engine.py  # Central engine (Sim + Hardware bridge)
        ├── physics/
        │   └── quad_physics.py   # 6-DOF non-linear flight dynamics, wind & battery
        ├── autopilot/
        │   ├── pid.py            # Discrete PID controllers
        │   └── autopilot.py      # State machine (Takeoff, Land, RTH, PosHold, Mission)
        ├── navigation/
        │   └── geodesy.py        # WGS-84 GPS coordinate transformation & presets
        ├── missions/
        │   └── mission_manager.py# Waypoint mission sequencer & progress tracker
        ├── hardware/
        │   └── mavlink_bridge.py # Pymavlink serial & UDP hardware bridge
        └── web/                  # Photorealistic Web Ground Control Station (GCS)
            ├── index.html        # Main GCS Cockpit layout
            ├── styles.css        # Futuristic avionics glassmorphism design system
            ├── drone3d.js        # Three.js photorealistic 3D Quadcopter with blur props
            ├── hud.js            # 60fps Canvas 2D aviation Heads-Up Display
            ├── map.js            # Leaflet real-world satellite map & waypoint planner
            └── app.js            # Central GCS JavaScript controller & audio synth
```

---

AeroSim is built for extreme precision, high visual fidelity, and seamless real-world aerial operations!
