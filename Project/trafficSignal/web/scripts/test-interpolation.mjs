import assert from "node:assert/strict";
import { interpolateVehicle, VehicleInterpolationBuffer } from "../src/vehicleInterpolation.js";

const vehicle = (overrides = {}) => ({
  vehicle_id: "car-1", x_m: 0, y_m: 0, angle_degrees: 0, speed_mps: 10, lane_id: "north", type_id: "sedan", ...overrides,
});

const northStart = vehicle();
const northEnd = vehicle({ y_m: 10 });
assert.equal(interpolateVehicle(northStart, northEnd, 0, 1).y_m, 0, "Hermite interpolation preserves its start endpoint");
assert.equal(interpolateVehicle(northStart, northEnd, 1, 1).y_m, 10, "Hermite interpolation preserves its end endpoint");
assert.equal(interpolateVehicle(northStart, northEnd, 0.5, 1).y_m, 5, "constant-speed travel remains linear");

const wrappedHeading = interpolateVehicle(vehicle({ angle_degrees: 350 }), vehicle({ angle_degrees: 10 }), 0.5, 1);
assert.ok(wrappedHeading.angle_degrees < 0.001 || wrappedHeading.angle_degrees > 359.999, "heading takes the shortest path over north");

const buffer = new VehicleInterpolationBuffer();
buffer.push(0, [vehicle()], "connected", 4, 0);
buffer.push(1, [vehicle({ y_m: 10 })], "connected", 4, 1000);
assert.ok(Math.abs(buffer.sample(1000).vehicles[0].y_m - 4) < 0.001, "buffer uses speed-scaled 150 ms playback delay");

buffer.push(1, [vehicle({ y_m: 10 })], "paused", 4, 1100);
assert.equal(buffer.sample(1200).vehicles[0].y_m, 10, "pause displays the latest actual SUMO state");
buffer.push(1, [vehicle({ y_m: 10 })], "connected", 4, 1300);
assert.equal(buffer.sample(1300).vehicles[0].y_m, 10, "resume begins at the paused position");
buffer.push(2, [vehicle({ y_m: 20 })], "connected", 4, 1400);
assert.ok(buffer.sample(1400).vehicles[0].y_m >= 10, "resume delay ramp never rewinds a vehicle");

buffer.push(3, [vehicle({ vehicle_id: "car-1", y_m: 30 }), vehicle({ vehicle_id: "new-car" })], "connected", 4, 1500);
assert.ok(!buffer.sample(1500).vehicles.some((entry) => entry.vehicle_id === "new-car"), "new vehicles wait until their spawn timestamp");
buffer.push(4, [vehicle({ vehicle_id: "new-car", y_m: 1 })], "connected", 4, 1600);
assert.ok(buffer.sample(1600).vehicles.some((entry) => entry.vehicle_id === "car-1"), "departing vehicles remain until their despawn timestamp");
buffer.push(4, [vehicle({ vehicle_id: "new-car", y_m: 1 })], "paused", 4, 1700);
assert.ok(!buffer.sample(1700).vehicles.some((entry) => entry.vehicle_id === "car-1"), "despawn removes vehicles at the latest paused state");
buffer.push(0, [vehicle({ y_m: -5 })], "connecting", 1, 1800);
assert.equal(buffer.sample(1800).vehicles[0].y_m, -5, "simulation time rollback clears stale run history");

console.log("vehicle interpolation: 12 assertions passed");
