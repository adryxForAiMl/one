const INTERPOLATION_DELAY_SECONDS = 0.15;
const HISTORY_SECONDS = 6;

function headingVelocity(vehicle) {
  const radians = (vehicle.angle_degrees * Math.PI) / 180;
  return {
    x: Math.cos(radians) * Math.max(0, vehicle.speed_mps),
    y: Math.sin(radians) * Math.max(0, vehicle.speed_mps),
  };
}

function lerp(a, b, t) {
  return a + (b - a) * t;
}

function interpolateAngle(from, to, t) {
  const delta = ((to - from + 540) % 360) - 180;
  return (from + delta * t + 360) % 360;
}

/**
 * SUMO snapshots can jitter slightly between frames when heading or speed changes
 * under load. Linear interpolation between the two actual map positions keeps the
 * rendered motion stable and avoids the overshoot that caused the vehicle to
 * appear to vibrate back and forth while moving.
 */
function interpolateVehicleInto(result, from, to, fraction) {
  const t = Math.max(0, Math.min(1, fraction));

  result.vehicle_id = from.vehicle_id;
  result.x_m = lerp(from.x_m, to.x_m, t);
  result.y_m = lerp(from.y_m, to.y_m, t);
  result.angle_degrees = interpolateAngle(from.angle_degrees, to.angle_degrees, t);
  result.speed_mps = lerp(from.speed_mps, to.speed_mps, t);
  result.lane_id = t < 1 ? from.lane_id : to.lane_id;
  result.type_id = t < 1 ? from.type_id : to.type_id;
  return result;
}

export function interpolateVehicle(from, to, fraction, durationSeconds) {
  return interpolateVehicleInto({ ...from }, from, to, fraction, durationSeconds);
}

function advanceVehicleInto(result, vehicle, seconds) {
  const velocity = headingVelocity(vehicle);
  result.vehicle_id = vehicle.vehicle_id;
  result.x_m = vehicle.x_m + velocity.x * seconds;
  result.y_m = vehicle.y_m + velocity.y * seconds;
  result.angle_degrees = vehicle.angle_degrees;
  result.speed_mps = vehicle.speed_mps;
  result.lane_id = vehicle.lane_id;
  result.type_id = vehicle.type_id;
  return result;
}

/**
 * Retains SUMO snapshots in simulation time and samples the scene 150 ms of
 * playback behind the latest state. Pause freezes at the latest actual frame;
 * resume ramps the delay in so it never rewinds the rendered scene.
 */
export class VehicleInterpolationBuffer {
  constructor() {
    this.frames = [];
    this.status = "idle";
    this.speed = 1;
    this.resumeStartedAt = null;
    this.renderedVehicles = [];
    this.renderedById = new Map();
    this.sampleNumber = 0;
  }

  reset() {
    this.frames = [];
    this.status = "idle";
    this.resumeStartedAt = null;
    this.renderedVehicles.length = 0;
    this.renderedById.clear();
    this.sampleNumber = 0;
  }

  push(simulationTime, vehicles, status, speed, receivedAtMs) {
    if (!Number.isFinite(simulationTime)) {
      if (["idle", "stopped", "completed", "disconnected"].includes(status)) this.reset();
      this.status = status;
      return;
    }

    const now = Number.isFinite(receivedAtMs) ? receivedAtMs : performance.now();
    const previousStatus = this.status;
    const latest = this.frames.at(-1);
    if (latest && simulationTime < latest.simulationTime - 0.001) this.reset();

    this.status = status;
    this.speed = Number.isFinite(speed) ? Math.max(0.5, Math.min(8, speed)) : 1;
    if (status === "paused") this.resumeStartedAt = null;
    else if (status === "connected" && previousStatus === "paused") this.resumeStartedAt = now;

    const frame = {
      simulationTime,
      receivedAtMs: now,
      vehicles: new Map(vehicles.map((vehicle) => [vehicle.vehicle_id, vehicle])),
    };
    const last = this.frames.at(-1);
    if (last && Math.abs(last.simulationTime - simulationTime) < 0.0001) this.frames[this.frames.length - 1] = frame;
    else this.frames.push(frame);

    const oldestTime = simulationTime - HISTORY_SECONDS;
    while (this.frames.length > 2 && this.frames[1].simulationTime < oldestTime) this.frames.shift();
  }

  sample(nowMs) {
    const latest = this.frames.at(-1);
    this.renderedVehicles.length = 0;
    if (!latest) return { simulationTime: null, vehicles: this.renderedVehicles };
    if (this.status !== "connected" || this.frames.length < 2) {
      return this.copyFrame(latest);
    }

    const now = Number.isFinite(nowMs) ? nowMs : performance.now();
    const elapsedSeconds = Math.max(0, (now - latest.receivedAtMs) / 1000);
    const estimatedCurrentTime = latest.simulationTime + elapsedSeconds * this.speed;
    const resumeFactor = this.resumeStartedAt === null
      ? 1
      : Math.min(1, Math.max(0, (now - this.resumeStartedAt) / (INTERPOLATION_DELAY_SECONDS * 1000)));
    const targetTime = Math.min(
      latest.simulationTime,
      estimatedCurrentTime - INTERPOLATION_DELAY_SECONDS * this.speed * resumeFactor,
    );

    if (targetTime <= this.frames[0].simulationTime) {
      return this.copyFrame(this.frames[0]);
    }

    for (let index = 0; index < this.frames.length - 1; index += 1) {
      const from = this.frames[index];
      const to = this.frames[index + 1];
      if (targetTime > to.simulationTime) continue;
      const duration = to.simulationTime - from.simulationTime;
      if (duration <= 0) continue;
      const fraction = Math.max(0, Math.min(1, (targetTime - from.simulationTime) / duration));
      for (const vehicle of from.vehicles.values()) {
        const next = to.vehicles.get(vehicle.vehicle_id);
        const output = this.getRenderedVehicle(vehicle.vehicle_id);
        this.renderedVehicles.push(next
          ? interpolateVehicleInto(output, vehicle, next, fraction, duration)
          : advanceVehicleInto(output, vehicle, Math.max(0, targetTime - from.simulationTime)));
      }
      this.pruneRenderedVehicles();
      return { simulationTime: targetTime, vehicles: this.renderedVehicles };
    }

    return this.copyFrame(latest);
  }

  getRenderedVehicle(id) {
    let vehicle = this.renderedById.get(id);
    if (!vehicle) {
      vehicle = { vehicle_id: id, x_m: 0, y_m: 0, angle_degrees: 0, speed_mps: 0, lane_id: "", type_id: "" };
      this.renderedById.set(id, vehicle);
    }
    vehicle.__lastSeen = this.sampleNumber;
    return vehicle;
  }

  copyFrame(frame) {
    for (const vehicle of frame.vehicles.values()) {
      const output = this.getRenderedVehicle(vehicle.vehicle_id);
      output.x_m = vehicle.x_m;
      output.y_m = vehicle.y_m;
      output.angle_degrees = vehicle.angle_degrees;
      output.speed_mps = vehicle.speed_mps;
      output.lane_id = vehicle.lane_id;
      output.type_id = vehicle.type_id;
      this.renderedVehicles.push(output);
    }
    this.pruneRenderedVehicles();
    return { simulationTime: frame.simulationTime, vehicles: this.renderedVehicles };
  }

  pruneRenderedVehicles() {
    this.sampleNumber += 1;
    if (this.sampleNumber % 120 !== 0) return;
    for (const [id, vehicle] of this.renderedById) {
      if (vehicle.__lastSeen !== this.sampleNumber - 1) this.renderedById.delete(id);
    }
  }
}
