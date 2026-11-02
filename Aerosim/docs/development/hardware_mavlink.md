# Connecting Physical Drone Hardware via MAVLink

AeroSim allows flying real physical drones using the MAVLink v2.0 protocol over USB Serial or UDP.

## Hardware Requirements
- Multirotor flight controller running **ArduPilot** (Copter) or **PX4 Autopilot**.
- Telemetry link:
  - USB Cable connecting flight controller to computer.
  - 433MHz / 915MHz SiK Telemetry Radio paired with computer.
  - ESP32 / WiFi telemetry module broadcasting on UDP port `14550`.

## Connection Steps

### 1. Serial Port Connection (USB / Telemetry Radio)
1. Plug in the USB cable or Telemetry Radio receiver into your computer.
2. In the AeroSim top navigation bar, click **"⚡ Connect Real Drone"**.
3. Select your serial port (e.g., `/dev/cu.usbserial-110` or `/dev/ttyUSB0`).
4. Select Baud Rate:
   - `115200` for direct USB Pixhawk connection.
   - `57600` for SiK Radio telemetry.
5. Click **"Connect to Real Drone"**.

### 2. UDP WiFi / SITL Connection
1. Ensure the drone or companion computer is on the same local network.
2. Direct MAVLink packets to `udp:0.0.0.0:14550`.
3. In AeroSim, select `udpin:0.0.0.0:14550`.
4. Click **"Connect to Real Drone"**.

## Supported MAVLink Commands
- `MAV_CMD_COMPONENT_ARM_DISARM`: Arm and Disarm motors.
- `MAV_CMD_NAV_TAKEOFF`: Autonomous takeoff to target altitude.
- `MAV_CMD_NAV_LAND`: Controlled descent and auto-disarm.
- `MAV_CMD_NAV_RETURN_TO_LAUNCH`: Return to home GPS launch location.
- `RC_CHANNELS_OVERRIDE` / `MANUAL_CONTROL`: Manual stick steering from AeroSim joysticks or USB Gamepad.
