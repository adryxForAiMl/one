"use client";

import dynamic from "next/dynamic";
import { AnimatePresence, motion } from "framer-motion";
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  CloudRain,
  Compass,
  Pause,
  Play,
  Radio,
  RotateCcw,
  Signal,
  TriangleAlert,
  Waves,
  Wind,
} from "lucide-react";
import { useEffect, useState } from "react";
import Starfield from "@/components/Starfield";
import type {
  CivicEvent,
  FeedHealth,
  FeedType,
  LiveSnapshot,
  PulseResponse,
  ReplayResponse,
  ZonePulse,
} from "@/lib/types";

const CityMap = dynamic(() => import("./CityMap"), {
  ssr: false,
  loading: () => <div className="map-loading">Loading city map…</div>,
});

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8010";
const feedLabels: Record<FeedType, string> = {
  weather: "Weather",
  transit: "Transit",
  complaints: "Resident reports",
};

const fallbackSnapshot: LiveSnapshot = {
  pulse: {
    as_of: new Date().toISOString(),
    city: "Rajasthan",
    top_summary: "A simulated pattern is worth watching around Jaipur.",
    zones: [
      { zone_id: "zone-1", name: "Ajmer", pulse_score: 23, status: "calm", summary: "No strong cross-feed pattern is showing.", active_anomalies: 0, event_count_24h: 3, available_feeds: ["weather", "transit", "complaints"], stale_feeds: [] },
      { zone_id: "zone-2", name: "Jodhpur", pulse_score: 18, status: "calm", summary: "No strong cross-feed pattern is showing.", active_anomalies: 0, event_count_24h: 3, available_feeds: ["weather", "transit", "complaints"], stale_feeds: [] },
      { zone_id: "zone-3", name: "Jaipur", pulse_score: 81, status: "elevated", summary: "Resident reports are rising alongside a weather alert and transit delays. These signals may be linked, but this does not establish a cause.", active_anomalies: 1, event_count_24h: 7, available_feeds: ["weather", "transit", "complaints"], stale_feeds: [] },
    ],
  },
  feeds: [
    { name: "weather", status: "stale", source_mode: "waiting for API", last_success_at: null, stale_after_seconds: 28800, message: "Waiting for the backend." },
    { name: "transit", status: "ok", source_mode: "synthetic", last_success_at: null, stale_after_seconds: 300, message: "Synthetic demo feed." },
    { name: "complaints", status: "ok", source_mode: "synthetic", last_success_at: null, stale_after_seconds: 180, message: "Synthetic demo feed." },
  ],
  anomalies: [],
  recent_events: [],
};

function statusColor(status: ZonePulse["status"]): string {
  return status === "elevated" ? "coral" : status === "watch" ? "amber" : "mint";
}

function eventLabel(event: CivicEvent): string {
  const category = event.raw_payload.category;
  const delay = event.raw_payload.delay_minutes;
  const rain = event.raw_payload.precipitation_mm;
  if (event.feed_type === "weather") return `Rainfall observation${typeof rain === "number" ? ` · ${rain} mm` : ""}`;
  if (event.feed_type === "transit") return `Transit delay${typeof delay === "number" ? ` · ${delay} min` : ""}`;
  return typeof category === "string" ? `Resident report · ${category}` : "Resident report received";
}

function timeAgo(timestamp: string | null, currentTime: number): string {
  if (!timestamp) return "Awaiting data";
  if (!currentTime) return "Just now";
  const minutes = Math.max(0, Math.floor((currentTime - new Date(timestamp).getTime()) / 60_000));
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes}m ago`;
  return `${Math.floor(minutes / 60)}h ago`;
}

export default function Dashboard() {
  const [snapshot, setSnapshot] = useState<LiveSnapshot>(fallbackSnapshot);
  const [connection, setConnection] = useState<"connecting" | "live" | "reconnecting">("connecting");
  const [selectedZoneId, setSelectedZoneId] = useState("zone-3");
  const [expandedZone, setExpandedZone] = useState<string | null>(null);
  const [replay, setReplay] = useState<ReplayResponse | null>(null);
  const [replayValue, setReplayValue] = useState(100);
  const [isReplaying, setIsReplaying] = useState(false);
  const [notice, setNotice] = useState("");
  const [clockMs, setClockMs] = useState(0);

  const replayEndMs = replay?.events.reduce(
    (latest, event) => Math.max(latest, new Date(event.timestamp).getTime()),
    0,
  ) ?? 0;
  const replayStartMs = replayEndMs - 72 * 60 * 60 * 1000;
  const replayScenarioStartMs = replayEndMs - 4 * 60 * 1000;
  const replayCutoff = replay
    ? new Date(replayValue <= 80
      ? replayStartMs + (replayScenarioStartMs - replayStartMs) * replayValue / 80
      : replayScenarioStartMs + (replayEndMs - replayScenarioStartMs) * (replayValue - 80) / 20)
    : null;
  const replayedEvents = replay && replayCutoff
    ? replay.events.filter((event) => new Date(event.timestamp) <= replayCutoff)
    : [];
  const replayHeroFeeds = new Set(replayedEvents
    .filter((event) => event.zone_id === "zone-3" && event.raw_payload.source === "CityPulse seeded hero scenario")
    .map((event) => event.feed_type));
  const replayStory = replayNarrative(replayHeroFeeds);
  const displayZones = snapshot.pulse.zones.map((zone) => {
    if (!replay || zone.zone_id !== "zone-3") return zone;
    const stage: ZonePulse["status"] = replayHeroFeeds.has("complaints")
      ? "elevated"
      : replayHeroFeeds.has("transit")
        ? "watch"
        : replayHeroFeeds.has("weather")
          ? "watch"
          : "calm";
    const score = replayHeroFeeds.has("complaints")
      ? 83
      : replayHeroFeeds.has("transit")
        ? 55
        : replayHeroFeeds.has("weather")
          ? 35
          : 18;
    return {
      ...zone,
      pulse_score: score,
      status: stage,
      active_anomalies: replayHeroFeeds.has("complaints") ? 1 : 0,
      summary: replayStory,
    };
  });
  const selectedZone = displayZones.find((zone) => zone.zone_id === selectedZoneId) ?? displayZones[0];
  const heroAnomaly = snapshot.anomalies.find((anomaly) => anomaly.zone_id === selectedZoneId) ?? snapshot.anomalies[0];
  const cityScore = displayZones.length
    ? Math.round(displayZones.reduce((sum, zone) => sum + zone.pulse_score, 0) / displayZones.length)
    : 0;
  const eventStream = (replay ? replayedEvents : snapshot.recent_events).slice(-9).reverse();
  const visibleAnomaly = replay
    ? replayHeroFeeds.has("complaints") ? heroAnomaly : null
    : heroAnomaly;

  useEffect(() => {
    const updateClock = () => setClockMs(Date.now());
    updateClock();
    const interval = setInterval(updateClock, 15_000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    let closed = false;
    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let fallbackTimer: ReturnType<typeof setInterval> | null = null;
    let backoff = 1000;

    const applySnapshot = (value: LiveSnapshot) => {
      if (!closed) setSnapshot(value);
    };

    const fetchSnapshot = async () => {
      try {
        const [pulseResponse, feedsResponse, zoneResponse] = await Promise.all([
          fetch(`${API_URL}/api/pulse`, { cache: "no-store" }),
          fetch(`${API_URL}/api/feeds/status`, { cache: "no-store" }),
          fetch(`${API_URL}/api/zone/zone-3`, { cache: "no-store" }),
        ]);
        if (!pulseResponse.ok || !feedsResponse.ok || !zoneResponse.ok) throw new Error("API unavailable");
        const [pulse, feeds, zone] = await Promise.all([
          pulseResponse.json() as Promise<PulseResponse>,
          feedsResponse.json() as Promise<FeedHealth[]>,
          zoneResponse.json(),
        ]);
        applySnapshot({ pulse, feeds, anomalies: zone.anomalies, recent_events: zone.feeds });
      } catch {
        if (!closed) setConnection("reconnecting");
      }
    };

    const connect = () => {
      if (closed) return;
      try {
        const socketUrl = API_URL.replace(/^http/, "ws") + "/ws/pulse";
        socket = new WebSocket(socketUrl);
        socket.onopen = () => {
          backoff = 1000;
          if (!closed) setConnection("live");
          if (fallbackTimer) clearInterval(fallbackTimer);
          fallbackTimer = null;
        };
        socket.onmessage = (message) => {
          try {
            const next = JSON.parse(message.data) as LiveSnapshot;
            if (next.pulse && next.feeds) applySnapshot(next);
          } catch {
            setConnection("reconnecting");
          }
        };
        socket.onerror = () => socket?.close();
        socket.onclose = () => {
          if (closed) return;
          setConnection("reconnecting");
          if (!fallbackTimer) fallbackTimer = setInterval(fetchSnapshot, 10_000);
          reconnectTimer = setTimeout(connect, backoff);
          backoff = Math.min(backoff * 2, 15_000);
        };
      } catch {
        setConnection("reconnecting");
        if (!fallbackTimer) fallbackTimer = setInterval(fetchSnapshot, 10_000);
        reconnectTimer = setTimeout(connect, backoff);
      }
    };

    void fetchSnapshot();
    connect();
    return () => {
      closed = true;
      socket?.close();
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (fallbackTimer) clearInterval(fallbackTimer);
    };
  }, []);

  useEffect(() => {
    if (!isReplaying) return;
    const timer = setInterval(() => {
      setReplayValue((value) => {
        if (value >= 100) {
          setIsReplaying(false);
          return 100;
        }
        return Math.min(100, value + 1);
      });
    }, 110);
    return () => clearInterval(timer);
  }, [isReplaying]);

  const toggleFeed = async (feed: FeedHealth) => {
    try {
      const response = await fetch(`${API_URL}/api/debug/feed/${feed.name}/toggle`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ down: feed.status !== "down" }),
      });
      if (!response.ok) throw new Error("Feed toggle failed");
      setNotice(`${feedLabels[feed.name]} feed ${feed.status === "down" ? "restored" : "paused"} for the demo.`);
      window.setTimeout(() => setNotice(""), 3200);
    } catch {
      setNotice("Could not reach the API. The dashboard remains in its last known state.");
      window.setTimeout(() => setNotice(""), 3600);
    }
  };

  const loadReplay = async () => {
    try {
      const response = await fetch(`${API_URL}/api/replay?range=72h`, { cache: "no-store" });
      if (!response.ok) throw new Error("Replay unavailable");
      setReplay((await response.json()) as ReplayResponse);
      setReplayValue(0);
      setIsReplaying(true);
    } catch {
      setNotice("Replay data is unavailable while the backend is disconnected.");
      window.setTimeout(() => setNotice(""), 3600);
    }
  };

  const selectedColor = statusColor(selectedZone?.status ?? "calm");
  return (
    <>
    <Starfield />
    <main className="dashboard-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="CityPulse home">
          <span className="brand-mark"><Waves size={19} strokeWidth={2.2} /></span>
          <span>city<span className="brand-accent">pulse</span></span>
          <span className="brand-edition">FIELD EDITION / 01</span>
        </a>
        <div className="topbar-right">
          <span className="location-chip"><Compass size={14} /> RAJASTHAN, IN</span>
          <span className={`connection-chip ${connection}`}><i />{connection === "live" ? "LIVE STREAM" : connection === "connecting" ? "CONNECTING" : "RECONNECTING"}</span>
            <span className="clock">{clockMs ? new Intl.DateTimeFormat("en-IN", { hour: "2-digit", minute: "2-digit", timeZone: "Asia/Kolkata" }).format(new Date(clockMs)) : "--:--"} IST</span>
        </div>
      </header>

      <section className="overview" id="top">
        <div className="overview-copy">
          <div className="eyebrow"><span className="eyebrow-line" /> REGIONAL HEALTH / LIVE OVERVIEW</div>
          <h1>{replay ? replayHeadline(replayHeroFeeds) : snapshot.anomalies.length ? "One Rajasthan district has a pattern worth watching." : cityScore >= 65 ? "Regional signals need attention." : cityScore >= 35 ? "Activity is building across the region." : "The region is moving steadily."}</h1>
          <p className="lead-summary">{replay ? replayStory : snapshot.pulse.top_summary}</p>
          <div className="overview-meta">
            <span><Activity size={14} /> {snapshot.pulse.zones.length} monitored zones</span>
            <span className="meta-divider" />
            <span>Updated {timeAgo(snapshot.pulse.as_of, clockMs)}</span>
            <span className="simulated-label">SYNTHETIC DEMO SIGNALS</span>
          </div>
        </div>
        <div className={`pulse-display ${cityScore >= 65 ? "pulse-hot" : cityScore >= 35 ? "pulse-warm" : "pulse-calm"}`}>
          <motion.div
            className="pulse-orbit orbit-one"
            animate={{ scale: [0.92, 1.12, 0.92], opacity: [0.3, 0.07, 0.3] }}
            transition={{ duration: cityScore >= 65 ? 2.2 : 4, repeat: Infinity, ease: "easeInOut" }}
          />
          <motion.div
            className="pulse-orbit orbit-two"
            animate={{ scale: [1.08, 0.92, 1.08], opacity: [0.12, 0.32, 0.12] }}
            transition={{ duration: cityScore >= 65 ? 2.2 : 4, repeat: Infinity, ease: "easeInOut" }}
          />
          <div className="pulse-core">
            <Waves size={27} />
            <strong>{cityScore}</strong>
            <span>REGION PULSE</span>
          </div>
          <span className="pulse-caption">{cityScore >= 65 ? "ELEVATED" : cityScore >= 35 ? "WATCH" : "CALM"}</span>
        </div>
        <div className="overview-index">
          <span className="index-label">PULSE INDEX</span>
          <strong>{String(cityScore).padStart(2, "0")}<small> / 100</small></strong>
          <span className="index-footnote">Relative activity · not a probability</span>
          <div className="index-trend"><ArrowUpRight size={15} /> Pattern concentration <b>{snapshot.anomalies.length ? "increasing" : "steady"}</b></div>
        </div>
      </section>

      <section className="feed-health" aria-label="Feed health">
        <div className="feed-health-heading"><Radio size={15} /><span>FEED HEALTH</span></div>
        {snapshot.feeds.map((feed) => (
          <button className={`feed-health-item ${feed.status}`} key={feed.name} onClick={() => void toggleFeed(feed)} title={`${feed.message} Click to ${feed.status === "down" ? "restore" : "pause"} this feed for the demo.`}>
            <span className="health-dot" />
            <span className="health-name">{feedLabels[feed.name]}</span>
            <span className="health-state">{feed.status === "ok" ? "LIVE" : feed.status === "stale" ? "STALE" : "DOWN"}</span>
            <span className="health-mode">{feed.source_mode}</span>
          </button>
        ))}
        <span className="health-hint">Click a feed to simulate an outage</span>
      </section>

      <div className="dashboard-grid">
        <section className="map-panel glass-panel">
          <div className="panel-heading">
            <div><span className="panel-kicker">RAJASTHAN / SPATIAL VIEW</span><h2>Regional pulse</h2></div>
            <span className="map-live-tag"><i /> LIVE</span>
          </div>
          <div className="map-wrap">
            <CityMap zones={displayZones} selectedZone={selectedZoneId} onSelectZone={setSelectedZoneId} />
            <div className="map-scale"><span>LOW ACTIVITY</span><i /><i /><i /><span>HIGH</span></div>
          </div>
          <div className="map-legend">
            <span><i className="legend-dot mint" /> Calm</span><span><i className="legend-dot amber" /> Watch</span><span><i className="legend-dot coral" /> Elevated</span>
            <span className="map-attribution-note">Illustrative zone markers · OSM base map</span>
          </div>
        </section>

        <aside className="right-rail">
          <section className="signal-panel glass-panel">
            <div className="panel-heading compact-heading">
              <div><span className="panel-kicker">CROSS-FEED SIGNAL</span><h2>{visibleAnomaly ? "A possible link" : "No active link"}</h2></div>
              <TriangleAlert size={18} className={visibleAnomaly ? "alert-icon" : "quiet-icon"} />
            </div>
            {visibleAnomaly ? (
              <motion.div key={`${visibleAnomaly.zone_id}-${visibleAnomaly.confidence}`} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
                <div className="causation-badge"><span className="badge-symbol">↗</span><span>POSSIBLE LINK <b>·</b> NOT CONFIRMED</span></div>
                <p className="anomaly-note">{visibleAnomaly.plain_language_note}</p>
                <div className="confidence-row"><span>Signal confidence</span><strong>{Math.round(visibleAnomaly.confidence * 100)}<small>%</small></strong></div>
                <div className="confidence-track"><span style={{ width: `${visibleAnomaly.confidence * 100}%` }} /></div>
                <div className="signal-sources">
                  {visibleAnomaly.feeds_involved.map((feed) => <span key={feed}>{feedLabels[feed]}</span>)}
                </div>
              </motion.div>
            ) : (
              <p className="quiet-copy">Signals are being monitored. A link appears when multiple feeds show an unusual pattern in the same zone.</p>
            )}
          </section>

          <section className="selected-zone-panel glass-panel">
            <div className="panel-heading compact-heading">
              <div><span className="panel-kicker">SELECTED ZONE / {selectedZone?.zone_id.slice(-1) ?? "—"}</span><h2>{selectedZone?.name ?? "No zone"}</h2></div>
              <span className={`zone-score ${selectedColor}`}>{selectedZone?.pulse_score ?? 0}</span>
            </div>
            <p className="zone-summary">{replay && selectedZoneId === "zone-3" ? replayStory : selectedZone?.summary}</p>
            <div className="zone-stats"><div><strong>{selectedZone?.event_count_24h ?? 0}</strong><span>events / 24h</span></div><div><strong>{selectedZone?.active_anomalies ?? 0}</strong><span>possible links</span></div></div>
            <div className="mini-timeline" aria-label="Recent relative signal activity">
              {[24, 31, 28, 42, 36, 48, 43, 57, 49, 66, 73, 61, 82, 75, 88, 79].map((height, index) => <span key={index} style={{ height: `${Math.max(12, height * (0.35 + (selectedZone?.pulse_score ?? 0) / 120))}%` }} />)}
            </div>
            <span className="chart-caption"><span>24H SIGNAL ACTIVITY</span><span>Relative · illustrative</span></span>
          </section>
        </aside>
      </div>

      <section className="zones-section">
        <div className="section-heading"><div><span className="panel-kicker">DISTRICT MONITOR / 03</span><h2>Across Rajasthan</h2></div><span className="section-aside">Select a city to inspect its signals <ArrowDownRight size={15} /></span></div>
        <div className="zone-grid">
          {displayZones.map((zone, index) => <ZoneCard key={zone.zone_id} zone={zone} index={index} selected={expandedZone === zone.zone_id} onSelect={() => { setSelectedZoneId(zone.zone_id); setExpandedZone(expandedZone === zone.zone_id ? null : zone.zone_id); }} />)}
        </div>
        <AnimatePresence>
          {expandedZone && <motion.div className="zone-detail glass-panel" initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.32 }}>
            <div className="zone-detail-inner"><div><span className="panel-kicker">ZONE REASONING</span><h3>{snapshot.pulse.zones.find((zone) => zone.zone_id === expandedZone)?.name}</h3><p>{snapshot.pulse.zones.find((zone) => zone.zone_id === expandedZone)?.summary}</p></div><div className="detail-evidence">{snapshot.feeds.map((feed) => <span key={feed.name} className={feed.status}><i />{feedLabels[feed.name]} · {feed.status}</span>)}</div><button className="close-detail" onClick={() => setExpandedZone(null)} aria-label="Close zone detail">×</button></div>
          </motion.div>}
        </AnimatePresence>
      </section>

      <section className="bottom-grid">
        <section className="ticker-panel glass-panel">
          <div className="ticker-title"><span className="panel-kicker">INCOMING SIGNALS</span><span><i /> STREAM</span></div>
          <div className="ticker-list">
            {eventStream.length ? eventStream.map((event) => <div className="ticker-item" key={event.id}><span className={`ticker-icon ${event.feed_type}`}>{event.feed_type === "weather" ? <CloudRain size={15} /> : event.feed_type === "transit" ? <Wind size={15} /> : <Signal size={15} />}</span><span className="ticker-text"><b>{snapshot.pulse.zones.find((zone) => zone.zone_id === event.zone_id)?.name ?? event.zone_id}</b><span>{eventLabel(event)}</span></span><time>{timeAgo(event.timestamp, clockMs)}</time></div>) : <div className="empty-ticker">Waiting for incoming events…</div>}
          </div>
        </section>

        <section className="replay-panel glass-panel">
          <div className="panel-heading compact-heading"><div><span className="panel-kicker">HISTORICAL REPLAY / 72H</span><h2>Replay the pulse</h2></div><button className="replay-icon-button" onClick={() => { setReplayValue(0); setIsReplaying(true); }} title="Restart replay" aria-label="Restart replay"><RotateCcw size={15} /></button></div>
          <p className="replay-copy">Trace how weather, transit, and reports lined up across the last three days.</p>
          {replay ? <>
            <div className="replay-stage"><span className={replayHeroFeeds.has("weather") ? "replay-step active" : "replay-step"}><i /> Weather</span><span className="stage-connector" /><span className={replayHeroFeeds.has("transit") ? "replay-step active" : "replay-step"}><i /> Transit</span><span className="stage-connector" /><span className={replayHeroFeeds.has("complaints") ? "replay-step active" : "replay-step"}><i /> Reports</span></div>
            <input className="replay-range" aria-label="Replay timeline" type="range" min="0" max="100" value={replayValue} style={{ background: `linear-gradient(90deg, var(--mint) ${replayValue}%, rgba(255,255,255,0.14) ${replayValue}%)` }} onChange={(event) => { setReplayValue(Number(event.target.value)); setIsReplaying(false); }} />
            <div className="replay-labels"><span>72H AGO</span><span>{replayCutoff?.toLocaleString("en-IN", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}</span><span>NOW</span></div>
            <div className="replay-footer"><span>{replayedEvents.length} events in view</span><button onClick={() => { if (isReplaying) { setIsReplaying(false); return; } if (replayValue >= 100) setReplayValue(0); setIsReplaying(true); }}>{isReplaying ? <><Pause size={12} /> PAUSE</> : <><Play size={12} /> PLAY SCENARIO</>} <span>↗</span></button></div>
          </> : <button className="replay-start" onClick={() => void loadReplay()}><span><Activity size={16} /> Load 72-hour replay</span><span>↗</span></button>}
        </section>
      </section>

      <footer className="page-footer"><span>CITYPULSE / FIELD EDITION</span><span>Correlation is not causation · This dashboard is a demonstration, not an official alert service.</span><span>DATA WINDOW / 24H</span></footer>
      <AnimatePresence>{notice && <motion.div className="toast" role="status" initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 12, opacity: 0 }}>{notice}</motion.div>}</AnimatePresence>
    </main>
    </>
  );
}

function replayNarrative(feeds: Set<FeedType>): string {
  const hasWeather = feeds.has("weather");
  const hasTransit = feeds.has("transit");
  const hasComplaints = feeds.has("complaints");
  if (hasWeather && hasTransit && hasComplaints) return "Rainfall, transit delays, and resident reports overlap in Jaipur. These signals may be linked; replay does not establish a cause.";
  if (hasWeather && hasTransit) return "A rainfall signal and transit delays appear in the replay. Resident reports have not clustered yet.";
  if (hasWeather) return "A weather signal appears first in the replay. Other feeds have not shown a matching pattern yet.";
  return "Move through the timeline to see how the three feeds arrived in sequence.";
}

function replayHeadline(feeds: Set<FeedType>): string {
  if (feeds.has("complaints")) return "Three feeds overlap in Jaipur.";
  if (feeds.has("transit")) return "Transit delays join the weather signal.";
  if (feeds.has("weather")) return "A weather signal arrives first.";
  return "Replay begins with a quiet baseline.";
}

function ZoneCard({ zone, index, selected, onSelect }: { zone: ZonePulse; index: number; selected: boolean; onSelect: () => void }) {
  const color = statusColor(zone.status);
  return <motion.button className={`zone-card ${color} ${selected ? "selected" : ""}`} onClick={onSelect} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.07 }} layout>
    <span className="zone-card-top"><span className="zone-index">0{index + 1} / ZONE</span><span className={`zone-indicator ${color}`} /></span>
    <span className="zone-card-name">{zone.name}</span>
    <span className="zone-card-bottom"><span>{zone.status.toUpperCase()} <small>· {zone.event_count_24h} EVENTS</small></span><strong>{String(zone.pulse_score).padStart(2, "0")}</strong></span>
    {selected && <motion.span className="zone-card-underline" layoutId="zone-underline" />}
  </motion.button>;
}