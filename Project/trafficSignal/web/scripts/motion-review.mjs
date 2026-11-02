import { existsSync } from "node:fs";
import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const webUrl = process.env.TRAFFIC_WEB_URL ?? "http://127.0.0.1:5173";
const apiUrl = process.env.TRAFFIC_API_URL ?? "http://127.0.0.1:8000";
const defaultBrowser = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser";
const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ?? (existsSync(defaultBrowser) ? defaultBrowser : undefined);
const outputDir = resolve(process.env.TRAFFIC_AFTER_DIR ?? fileURLToPath(new URL("../../docs/visual/after", import.meta.url)));
const browser = await chromium.launch({ headless: process.env.TRAFFIC_HEADFUL !== "1", ...(executablePath ? { executablePath } : {}) });
const page = await browser.newPage({ viewport: { width: 2560, height: 1440 }, deviceScaleFactor: 1 });
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
page.on("console", (message) => { if (message.type() === "error") errors.push(message.text()); });

async function api(path, init) {
  const response = await fetch(`${apiUrl}${path}`, init);
  if (!response.ok) throw new Error(`${path} returned ${response.status}: ${await response.text()}`);
  return response.json();
}

const waitForTraffic = async (minimumVehicles, timeoutMs = 180_000) => {
  const deadline = Date.now() + timeoutMs;
  let lastState;
  while (Date.now() < deadline) {
    lastState = await api("/api/state", { cache: "no-store" });
    if (lastState.status === "connected" &&
      (lastState.controllers.fixed?.vehicles.length ?? 0) >= minimumVehicles &&
      (lastState.controllers.adaptive?.vehicles.length ?? 0) >= minimumVehicles) return lastState;
    if (["disconnected", "completed"].includes(lastState.status)) break;
    await page.waitForTimeout(250);
  }
  throw new Error(`Did not reach ${minimumVehicles} vehicles per scene: ${JSON.stringify({ status: lastState?.status, fixed: lastState?.controllers.fixed?.vehicles.length, adaptive: lastState?.controllers.adaptive?.vehicles.length, error: lastState?.error })}`);
};

try {
  await mkdir(outputDir, { recursive: true });
  await page.goto(webUrl, { waitUntil: "networkidle" });
  await page.waitForFunction(() => document.querySelector(".panel-bottom")?.textContent?.includes("API reachable"));
  await page.locator(".advanced-settings > summary").click();
  await page.locator("#quality").selectOption("high");
  const current = await api("/api/state", { cache: "no-store" });
  if (["connecting", "connected", "paused", "stopping"].includes(current.status)) {
    await api("/api/simulation/stop", { method: "POST" });
    await page.waitForTimeout(500);
  }
  await api("/api/simulation/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode: "compare", scenario: "rush_hour", seed: 42, duration_seconds: 3600,
      north_south_veh_per_hour: 7200, east_west_veh_per_hour: 7200, speed_multiplier: 8 }),
  });
  const stateAtLoad = await waitForTraffic(150);
  await page.evaluate(() => {
    window.__trafficRecordMotion = true;
    window.__trafficSceneDiagnostics?.["Fixed-time"]?.(true);
    window.__trafficSceneDiagnostics?.Adaptive?.(true);
  });
  await page.waitForTimeout(15_000);
  const state = await api("/api/state", { cache: "no-store" });
  const diagnostics = await page.evaluate(() => ({
    visibilityState: document.visibilityState,
    fixed: window.__trafficSceneDiagnostics?.["Fixed-time"]?.() ?? null,
    adaptive: window.__trafficSceneDiagnostics?.Adaptive?.() ?? null,
  }));
  const screenshot = "dashboard-motion-2560x1440.png";
  await page.screenshot({ path: resolve(outputDir, screenshot) });
  const report = {
    date: new Date().toISOString(),
    capture_engine: `Playwright ${browser.version()}${executablePath ? ` (${executablePath})` : ""}`,
    capture_mode: "headless Chromium; document visibility and WebGL renderer recorded",
    renderer_architecture: "one shared WebGL renderer with scissor-rendered comparison views; renderer.info counters are combined across both scenes",
    viewport: "2560x1440",
    quality: "high",
    requested_vehicle_floor_per_scene: 150,
    measurement_seconds_after_load: 15,
    position_error_definition: "Per animation frame: mean across continuing vehicles of the residual between rendered displacement and the previous rendered heading/speed prediction over the interpolated simulation-time delta.",
    simulation: {
      status: state.status, scenario: state.scenario, seed: state.seed,
      simulation_time_seconds: state.simulation_time_seconds,
      fixed_vehicles_at_load: stateAtLoad.controllers.fixed.vehicles.length,
      adaptive_vehicles_at_load: stateAtLoad.controllers.adaptive.vehicles.length,
      fixed_vehicles_at_capture: state.controllers.fixed?.vehicles.length ?? 0,
      adaptive_vehicles_at_capture: state.controllers.adaptive?.vehicles.length ?? 0,
    },
    screenshot,
    diagnostics,
    page_errors: errors,
  };
  await writeFile(resolve(outputDir, "motion-performance-report.json"), `${JSON.stringify(report, null, 2)}\n`);

  const trace = diagnostics.adaptive?.motion?.trace ?? [];
  const width = 1200;
  const height = 360;
  const pad = { left: 76, right: 24, top: 26, bottom: 48 };
  const values = trace.map((sample) => sample.meanPositionErrorMeters).filter(Number.isFinite);
  const maximum = Math.max(0.01, ...values);
  const plotWidth = width - pad.left - pad.right;
  const plotHeight = height - pad.top - pad.bottom;
  const points = values.map((value, index) => {
    const x = pad.left + (values.length < 2 ? 0 : index / (values.length - 1)) * plotWidth;
    const y = pad.top + plotHeight - (value / maximum) * plotHeight;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
  const grid = [0, 0.25, 0.5, 0.75, 1].map((fraction) => {
    const y = pad.top + plotHeight * fraction;
    const label = (maximum * (1 - fraction)).toFixed(3);
    return `<line x1="${pad.left}" y1="${y}" x2="${width - pad.right}" y2="${y}" stroke="#e4e9e3"/><text x="${pad.left - 10}" y="${y + 4}" text-anchor="end" fill="#626b60" font-size="12">${label}</text>`;
  }).join("\n");
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
  <rect width="100%" height="100%" fill="#fff"/>
  <text x="${pad.left}" y="18" fill="#252820" font-family="sans-serif" font-size="14">Adaptive · ${values.length} animation frames · ${report.measurement_seconds_after_load}s high-demand live run</text>
  ${grid}
  <polyline points="${points}" fill="none" stroke="#237a4b" stroke-width="1.6"/>
  <text x="${width / 2}" y="${height - 8}" text-anchor="middle" fill="#626b60" font-family="sans-serif" font-size="12">Rendered simulation time (s)</text>
  <text transform="translate(18 ${height / 2}) rotate(-90)" text-anchor="middle" fill="#626b60" font-family="sans-serif" font-size="12">Frame mean position prediction error (m)</text>
  </svg>`;
  await writeFile(resolve(outputDir, "frame-position-error.svg"), svg);
  console.log(JSON.stringify({
    status: state.status,
    simTime: state.simulation_time_seconds,
    fixedVehicles: report.simulation.fixed_vehicles_at_capture,
    adaptiveVehicles: report.simulation.adaptive_vehicles_at_capture,
    visibilityState: diagnostics.visibilityState,
    fixedFrameTime: diagnostics.fixed?.frameTimeMs,
    adaptiveFrameTime: diagnostics.adaptive?.frameTimeMs,
    adaptivePositionError: {
      samples: diagnostics.adaptive?.motion?.samples,
      meanMeters: diagnostics.adaptive?.motion?.meanFramePositionErrorMeters,
      p95Meters: diagnostics.adaptive?.motion?.p95FramePositionErrorMeters,
      plot: `${outputDir}/frame-position-error.svg`,
    },
    errors,
  }, null, 2));
  if (errors.length) process.exitCode = 1;
} finally {
  try { await api("/api/simulation/stop", { method: "POST" }); } catch {}
  await browser.close();
}
