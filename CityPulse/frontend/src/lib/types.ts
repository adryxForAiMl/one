export type FeedType = "weather" | "transit" | "complaints";
export type FeedStatusValue = "ok" | "stale" | "down";

export interface ZonePulse {
  zone_id: string;
  name: string;
  pulse_score: number;
  status: "calm" | "watch" | "elevated";
  summary: string;
  active_anomalies: number;
  event_count_24h: number;
  available_feeds: FeedType[];
  stale_feeds: FeedType[];
}

export interface PulseResponse {
  as_of: string;
  city: string;
  zones: ZonePulse[];
  top_summary: string;
}

export interface FeedHealth {
  name: FeedType;
  status: FeedStatusValue;
  source_mode: string;
  last_success_at: string | null;
  stale_after_seconds: number;
  message: string;
}

export interface CivicEvent {
  id: string;
  feed_type: FeedType;
  zone_id: string;
  lat: number;
  lon: number;
  timestamp: string;
  severity: number;
  raw_payload: Record<string, unknown>;
}

export interface Anomaly {
  zone_id: string;
  feeds_involved: FeedType[];
  confidence: number;
  plain_language_note: string;
  is_correlation_not_causation: true;
  observed_at: string;
}

export interface LiveSnapshot {
  pulse: PulseResponse;
  feeds: FeedHealth[];
  anomalies: Anomaly[];
  recent_events: CivicEvent[];
}

export interface ReplayResponse {
  range: string;
  events: CivicEvent[];
  hero_scenario: {
    zone_id: string;
    sequence: string[];
    simulated: boolean;
  };
}