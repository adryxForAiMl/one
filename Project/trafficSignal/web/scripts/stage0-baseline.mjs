import { existsSync } from "node:fs";
import { mkdir, writeFile } from "node:fs/promises";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";
import { chromium } from "playwright";

const webUrl = process.env.TRAFFIC_WEB_URL ?? "http://127.0.0.1:5173";
const apiUrl = process.env.TRAFFIC_API_URL ?? "http://127.0.0.1:8000";
const defaultBrowser = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser";
const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ?? (existsSync(defaultBrowser) ? defaultBrowser : undefined);
const outDir = resolve(process.env.TRAFFIC_BASELINE_DIR ?? fileURLToPath(new URL("../../docs/visual/baseline", import.meta.url)));
const browser = await chromium.launch({ headless: process.env.TRAFFIC_HEADFUL !== "1", ...(executablePath ? { executablePath } : {}) });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
const errors = [];
const failedResponses = [];
page.on("pageerror", (error) => errors.push(error.message));
page.on("console", (message) => { if (message.type() === "error") errors.push(message.text()); });
page.on("response", (response) => { if (response.status() >= 400) failedResponses.push({ status: response.status(), url: response.url() }); });

async function api(path, init) {
  const response = await fetch(`${apiUrl}${path}`, init);
  if (!response.ok) throw new Error(`${path} returned ${response.status}: ${await response.text()}`);
  return response.json();
}

async function state() {
  return api("/api/state", { cache: "no-store" });
}

try {
  await mkdir(outDir, { recursive: true });
  await page.goto(webUrl, { waitUntil: "networkidle" });
  await page.getByRole("button", { name: /start simulation/i }).waitFor({ state: "visible" });
  await page.waitForFunction(() => document.querySelector(".panel-bottom")?.textContent?.includes("API reachable"));

  const initial = await state();
  if (["connecting", "connected", "paused", "stopping"].includes(initial.status)) {
    await api("/api/simulation/stop", { method: "POST" });
    await page.waitForTimeout(500);
  }
  await api("/api/simulation/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode: "compare", scenario: "rush_hour", seed: 42, duration_seconds: 3600,
      north_south_veh_per_hour: 7200, east_west_veh_per_hour: 7200, speed_multiplier: 8 }),
  });
  const deadline = Date.now() + 180_000;
  let live;
  while (Date.now() < deadline) {
    live = await state();
    if ((live.controllers.fixed?.vehicles.length ?? 0) >= 100 && (live.controllers.adaptive?.vehicles.length ?? 0) >= 100) break;
    if (live.status === "disconnected" || live.error) throw new Error(`SUMO failed: ${live.error ?? live.status}`);
    await page.waitForTimeout(250);
  }
  if ((live?.controllers.fixed?.vehicles.length ?? 0) < 100 || (live?.controllers.adaptive?.vehicles.length ?? 0) < 100) {
    throw new Error(`Timed out waiting for demand: fixed=${live?.controllers.fixed?.vehicles.length}, adaptive=${live?.controllers.adaptive?.vehicles.length}`);
  }
  await api("/api/simulation/pause", { method: "POST" });
  await page.waitForFunction(() => document.querySelectorAll(".scene-grid canvas").length === 1 &&
    window.__trafficSceneDiagnostics?.["Fixed-time"] && window.__trafficSceneDiagnostics?.Adaptive);

  const measurements = [];
  for (const viewport of [{ width: 1440, height: 900 }, { width: 1920, height: 1080 }]) {
    await page.setViewportSize(viewport);
    await page.waitForTimeout(1000);
    await page.evaluate(() => {
      window.__trafficSceneDiagnostics?.["Fixed-time"]?.(true);
      window.__trafficSceneDiagnostics?.Adaptive?.(true);
    });
    await page.waitForTimeout(10_000);
    const diagnostics = await page.evaluate(() => ({
      visibilityState: document.visibilityState,
      fixed: window.__trafficSceneDiagnostics?.["Fixed-time"]?.() ?? null,
      adaptive: window.__trafficSceneDiagnostics?.Adaptive?.() ?? null,
    }));
    const file = `dashboard-${viewport.width}x${viewport.height}.png`;
    await page.screenshot({ path: resolve(outDir, file), fullPage: false });
    measurements.push({ viewport: `${viewport.width}x${viewport.height}`, screenshot: file, ...diagnostics });
  }
  live = await state();
  const report = {
    date: new Date().toISOString(),
    source_revision: execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim(),
    working_tree: "modified; see repository status for the full shared-workspace diff",
    capture_engine: `Playwright ${browser.version()}${executablePath ? ` (${executablePath})` : ""}`,
    capture_mode: process.env.TRAFFIC_HEADFUL === "1" ? "foreground headed browser" : "headless browser; document visibility and GPU renderer recorded below",
    measurement_window_seconds_per_viewport: 10,
    limitations: [
      "Browser-rendered frame intervals and performance.memory JavaScript heap are measured; OS process and GPU memory are not.",
      "The browser used the Apple Metal renderer, but this is not a MacBook Air certification run because the exact host model and device thermal state were not recorded.",
    ],
    simulation: {
      status: live.status, scenario: live.scenario, seed: live.seed,
      simulation_time_seconds: live.simulation_time_seconds,
      north_south_demand_veh_per_hour: 7200, east_west_demand_veh_per_hour: 7200,
      fixed_active_vehicles: live.controllers.fixed.vehicles.length,
      adaptive_active_vehicles: live.controllers.adaptive.vehicles.length,
    },
    viewports: measurements,
    page_errors: errors,
    failed_responses: failedResponses,
  };
  await writeFile(resolve(outDir, "performance-baseline.json"), `${JSON.stringify(report, null, 2)}\n`);
  console.log(JSON.stringify(report, null, 2));
  if (errors.length) process.exitCode = 1;
} finally {
  try { await api("/api/simulation/stop", { method: "POST" }); } catch {}
  await browser.close();
}
