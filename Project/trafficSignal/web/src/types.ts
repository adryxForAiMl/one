export type VehicleState = {
  vehicle_id: string;
  x_m: number;
  y_m: number;
  angle_degrees: number;
  speed_mps: number;
  lane_id: string;
  type_id: string;
};

export type MetricsState = {
  active_vehicles: number;
  completed_vehicles: number;
  total_queue_vehicles: number;
  queues_by_approach: Record<string, number>;
  average_wait_seconds: number;
  accumulated_delay_vehicle_seconds: number;
  average_speed_mps: number;
  phase_green_seconds: number;
  average_completed_trip_travel_time_seconds: number;
};

export type ControllerLiveState = {
  mode: string;
  metrics: MetricsState;
  signal: { phase: number; phase_state: string; green_seconds_remaining: number | null } | null;
  vehicles: VehicleState[];
  solver: {
    solver: string;
    status: string;
    converged: boolean;
    green_seconds: number[];
    objective_value: number;
    reason: string;
  } | null;
  flow_estimation: {
    method: string;
    matrix: number[][] | null;
    rhs: number[];
    detector_counts: Record<string, number>;
    detector_rates: Record<string, number>;
    interval_seconds: number;
    solution: number[] | null;
    status: string;
    rank: number;
    residual: number | null;
    row_operations: string[];
    used: boolean;
  } | null;
  decision_reason: string | null;
};

export type LiveState = {
  status: "idle" | "connecting" | "connected" | "paused" | "stopping" | "stopped" | "completed" | "disconnected";
  scenario: string | null;
  site_id?: string;
  disclaimer?: string;
  attribution?: string;
  seed: number | null;
  speed_multiplier: number;
  simulation_time_seconds: number | null;
  wall_elapsed_seconds: number | null;
  controllers: Record<string, ControllerLiveState>;
  error: string | null;
  results_summary: Record<string, {
    total_completed_trips: number;
    mean_queue_length: number;
    peak_95th_queue_length: number;
    mean_waiting_time: number;
    total_accumulated_delay: number;
    mean_speed_kmh: number;
    average_completed_trip_travel_time_seconds: number;
  }>;
};

export type SiteOption = {
  id: string;
  name: string;
  type: string;
  description: string;
  attribution: string | null;
};

export type SiteGeometry = {
  site_id: string;
  name: string;
  attribution: string;
  license: string;
  disclaimer: string;
  traffic_side: string;
  center_utm: { x: number; y: number; lat: number; lon: number };
  bounds_radius_m: number;
  lanes: Array<{
    id: string;
    edge_id: string;
    index: number;
    speed_mps: number;
    width_m: number;
    shape: [number, number][];
  }>;
  junctions: Array<{
    id: string;
    x: number;
    y: number;
    type: string;
    shape: [number, number][];
  }>;
  buildings: Array<{
    id: string;
    points: [number, number][];
    height_m: number;
    height_source: string;
    name: string;
  }>;
  central_feature: {
    x: number;
    y: number;
    radius_m: number;
    type: string;
    provenance: string;
  };
  decorative_scatter: Array<{
    x: number;
    y: number;
    type: string;
    provenance: string;
  }>;
  provenance: Record<string, any>;
};

export type Sample = {
  sim_time: number;
  fixed_queue?: number;
  adaptive_queue?: number;
  fixed_delay?: number;
  adaptive_delay?: number;
  fixed_wait?: number;
  adaptive_wait?: number;
  fixed_speed?: number;
  adaptive_speed?: number;
};
