import type { VehicleState } from "./trafficScene";

export function interpolateVehicle(from: VehicleState, to: VehicleState, fraction: number, durationSeconds: number): VehicleState;

export class VehicleInterpolationBuffer {
  constructor();
  reset(): void;
  push(simulationTime: number | null, vehicles: readonly VehicleState[], status: string, speed: number, receivedAtMs: number): void;
  sample(nowMs: number): { simulationTime: number | null; vehicles: VehicleState[] };
}
