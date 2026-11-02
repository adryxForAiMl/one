import { existsSync } from "node:fs";
import { mkdir, readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const baseUrl = process.env.TRAFFIC_WEB_URL ?? "http://127.0.0.1:5173";
const apiUrl = process.env.TRAFFIC_API_URL ?? "http://127.0.0.1:8000";
const outputDir = resolve(process.env.TRAFFIC_SCREENSHOT_DIR ?? fileURLToPath(new URL("../../docs/screenshots/", import.meta.url)));
await mkdir(outputDir, { recursive: true });

const defaultBrowser = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser";
const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ?? (existsSync(defaultBrowser) ? defaultBrowser : undefined);
const browser = await chromium.launch({ headless: true, ...(executablePath ? { executablePath } : {}) });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
const errors = [];
const expectedErrors = [];
let expectingPauseRejection = false;
const downloadedFiles = [];
const saveDownload = async (locator) => {
  const pending = page.waitForEvent("download");
  await locator.click();
  const file = await pending;
  const path = resolve(outputDir, file.suggestedFilename());
  await file.saveAs(path);
  const details = { name: file.suggestedFilename(), path, bytes: (await readFile(path)).byteLength };
  if (details.bytes === 0) throw new Error(`Empty download: ${details.name}`);
  downloadedFiles.push(details);
  return { ...details, content: await readFile(path, "utf8") };
};
const waitForApiState = async (predicate, timeoutMs = 30000) => {
  const deadline = Date.now() + timeoutMs;
  let lastState;
  while (Date.now() < deadline) {
    const response = await fetch(`${apiUrl}/api/state`, { cache: "no-store" });
    lastState = await response.json();
    if (predicate(lastState)) return lastState;
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(`Timed out waiting for API state: ${JSON.stringify(lastState)}`);
};
page.on("pageerror", (error) => errors.push(error.message));
page.on("close", () => console.log("Browser page closed during review"));
page.on("crash", () => console.log("Browser page crashed during review"));
page.on("console", (message) => {
  if (message.type() === "error") {
    if (expectingPauseRejection && /409/.test(message.text())) expectedErrors.push(message.text());
    else errors.push(message.text());
  }
});

try {
  await page.goto(baseUrl, { waitUntil: "networkidle" });
  await page.getByRole("button", { name: /start simulation/i }).waitFor({ state: "visible" });
  await page.waitForFunction(() => document.querySelector(".panel-bottom")?.textContent?.includes("API reachable"));
  if (!(await page.locator(".export-row").getByRole("button", { name: "CSV", exact: true }).isDisabled())) {
    throw new Error("CSV export should stay disabled until telemetry samples exist");
  }
  await page.locator(".advanced-settings > summary").click();
  const qualityOptions = await page.locator("#quality option").evaluateAll((options) => options.map((option) => option.value));
  if (qualityOptions.join(",") !== "ultra,high,medium,low") throw new Error(`Expected four quality tiers, found ${qualityOptions.join(",")}`);
  const automaticResolution = page.getByLabel("Automatic resolution");
  if (!(await automaticResolution.isChecked())) throw new Error("Automatic resolution should be enabled by default");
  await automaticResolution.uncheck();
  await automaticResolution.check();
  await page.locator("#quality").selectOption("ultra");
  await page.waitForFunction(() => Boolean(window.__trafficSceneDiagnostics?.["Fixed-time"]?.()));
  await page.locator("#quality").selectOption("medium");
  const cameraViews = page.locator(".camera-preset-control select");
  if (await cameraViews.count() !== 2) throw new Error("Expected a camera preset control on both comparison views");
  await cameraViews.first().selectOption("analytic");
  if (!(await cameraViews.nth(1).inputValue() === "analytic")) throw new Error("Camera preset did not synchronize across comparison views");
  await cameraViews.nth(1).selectOption("street");
  if (!(await cameraViews.first().inputValue() === "street")) throw new Error("Camera preset change from the second view did not synchronize");
  await cameraViews.first().selectOption("overview");
  const helpPopupPromise = page.waitForEvent("popup");
  await page.getByRole("link", { name: "Open API documentation in a new tab" }).click();
  const helpPopup = await helpPopupPromise;
  await helpPopup.waitForLoadState("domcontentloaded");
  if (!helpPopup.url().endsWith("/docs")) throw new Error("API documentation button did not open the API docs");
  await helpPopup.close();
  await page.locator("#duration").fill("75");
  if (await page.locator("#duration").inputValue() !== "75") throw new Error("Run length cannot be edited reliably");
  await page.getByRole("button", { name: /try a 60-second demo/i }).click();
  if (await page.locator("#duration").inputValue() !== "60") throw new Error("Quick demo did not update the run length control");
  const quickDemoState = await waitForApiState((state) => state.status === "connected" &&
    state.scenario === "balanced" && state.seed === 42 && state.controllers.fixed && state.controllers.adaptive);
  if (quickDemoState.speed_multiplier < 0.5) throw new Error("Quick demo did not apply a valid simulation speed");
  await page.waitForFunction(() => {
    const emptyLabels = [...document.querySelectorAll(".scene-empty")];
    return emptyLabels.length >= 2 && emptyLabels.every((element) => getComputedStyle(element).display === "none");
  }, null, { timeout: 45000 });
  if (await page.locator(".export-row").getByRole("button", { name: "CSV", exact: true }).isDisabled()) {
    throw new Error("CSV export should enable once telemetry samples arrive");
  }
  const freshStateBeforePause = await waitForApiState((state) => state.status === "connected" &&
    state.controllers.adaptive?.solver !== null && state.controllers.adaptive?.solver !== undefined &&
    state.simulation_time_seconds >= 20 && state.controllers.fixed?.vehicles.length >= 2 &&
    state.controllers.adaptive?.vehicles.length >= 2);
  expectingPauseRejection = true;
  await page.route(`${apiUrl}/api/simulation/pause`, (route) => route.fulfill({
    status: 409,
    contentType: "application/json",
    body: JSON.stringify({ detail: "Browser error-state check" }),
  }));
  await page.getByRole("button", { name: /pause/i }).click();
  await page.getByRole("alert").getByText("Browser error-state check").waitFor();
  await page.getByRole("button", { name: "Dismiss error" }).click();
  if (await page.getByRole("alert").count()) throw new Error("Dismiss error button did not clear the error banner");
  await page.unroute(`${apiUrl}/api/simulation/pause`);
  expectingPauseRejection = false;
  await page.getByRole("button", { name: /pause/i }).click();
  const liveState = await waitForApiState((state) => state.status === "paused");
  await page.waitForFunction(() => document.querySelector(".connection-pill")?.textContent?.includes("paused"));
  const adaptiveVehicles = liveState.controllers.adaptive?.vehicles ?? [];
  const liveDashboardModules = await Promise.all([
    page.getByRole("heading", { name: "Approach activity" }).count(),
    page.getByRole("heading", { name: "Fleet mix" }).count(),
    page.getByRole("heading", { name: "Traffic alerts" }).count(),
    page.getByLabel("Live signal phase sequence").count(),
  ]);
  if (liveDashboardModules.some((count) => count !== 1)) throw new Error("A live reference-inspired dashboard module is missing");
  const detectorRates = liveState.controllers.adaptive?.flow_estimation?.detector_rates;
  if (!detectorRates || !["North", "South", "East", "West"].every((direction) => typeof detectorRates[direction] === "number")) {
    throw new Error("SUMO induction-loop rates are missing by approach");
  }
  const performanceDownloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download performance report as JSON" }).click();
  const performanceDownload = await performanceDownloadPromise;
  const performancePath = resolve(outputDir, performanceDownload.suggestedFilename());
  await performanceDownload.saveAs(performancePath);
  const performanceReport = JSON.parse(await readFile(performancePath, "utf8"));
  if (performanceReport.schema_version !== 1 || !performanceReport.scenes["Fixed-time"] || !performanceReport.scenes.Adaptive ||
    performanceReport.renderer.architecture !== "one shared WebGLRenderer with two scissor viewports" ||
    typeof performanceReport.renderer.draw_calls !== "number" || typeof performanceReport.scenes.Adaptive.frameTimeMs.p99 !== "number" ||
    performanceReport.display.adaptive_resolution_enabled !== true || typeof performanceReport.display.current_resolution_scale !== "number") {
    throw new Error("Performance report is missing live scene, frame-time, renderer, or GPU fields");
  }
  const stateDownload = await saveDownload(page.getByRole("button", { name: "Download current state and observed history as JSON" }));
  const exportedState = JSON.parse(stateDownload.content);
  if (!exportedState.latest_state || !Array.isArray(exportedState.sampled_history)) throw new Error("Header JSON export has an unexpected payload");
  const headerCsv = await saveDownload(page.getByRole("button", { name: "Download observed telemetry history as CSV" }));
  if (!headerCsv.content.startsWith("simulation_time_seconds,fixed_queue")) throw new Error("Header CSV export has an unexpected payload");
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: "instant" }));
  await page.waitForTimeout(300);
  await page.screenshot({ path: resolve(outputDir, "dashboard-1440x900.png") });
  await page.setViewportSize({ width: 1920, height: 1080 });
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: "instant" }));
  await page.waitForTimeout(300);
  await page.screenshot({ path: resolve(outputDir, "dashboard-1920x1080.png") });
  await page.getByRole("button", { name: /resume/i }).click();
  await page.waitForFunction(() => document.querySelector(".connection-pill")?.textContent?.includes("connected"));
  const csvButtons = await page.getByRole("button", { name: "CSV", exact: true }).count();
  const jsonButtons = await page.getByRole("button", { name: "JSON", exact: true }).count();
  if (!csvButtons || !jsonButtons) throw new Error("CSV or JSON export controls are missing");
  const bottomCsv = await saveDownload(page.getByRole("button", { name: "CSV", exact: true }));
  const bottomJson = await saveDownload(page.getByRole("button", { name: "JSON", exact: true }));
  if (!bottomCsv.content.startsWith("simulation_time_seconds,") || !JSON.parse(bottomJson.content).latest_state) {
    throw new Error("Dashboard telemetry export buttons returned invalid data");
  }
  await page.getByRole("button", { name: /stop/i }).click();
  await page.waitForFunction(() => document.querySelector(".connection-pill")?.textContent?.includes("stopped"), null, { timeout: 15000 });
  await page.getByRole("button", { name: /reset/i }).click();
  await waitForApiState((state) => state.status === "idle");
  await page.locator("#mode").selectOption("adaptive");
  const singleModeHasFixedAdaptiveLegend = await page.locator(".approach-legend").count();
  const singleModeApproachColumnCount = await page.locator(".approach-row").first().locator("b").count();
  if (singleModeHasFixedAdaptiveLegend !== 0 || singleModeApproachColumnCount !== 1) {
    throw new Error("Single-controller mode still shows the comparison queue layout");
  }
  await page.locator(".reference-grid").scrollIntoViewIfNeeded();
  await page.screenshot({ path: resolve(outputDir, "dashboard-live-insights.png") });

  await page.locator("#mode").selectOption("compare");
  await page.locator("#duration").fill("15");
  await page.locator("#speed").selectOption("8");
  await page.getByRole("button", { name: "Start simulation" }).click();
  await waitForApiState((state) => state.status === "completed", 60000);
  await page.getByRole("button", { name: /saved/i }).click();
  await page.locator(".history-item").first().waitFor();
  await page.locator(".history-item").first().click();
  const selectedRunDownload = await saveDownload(page.getByRole("button", { name: "Export selected run" }));
  if (!JSON.parse(selectedRunDownload.content).summary) throw new Error("Selected run export omitted its summary");
  await page.getByRole("button", { name: "Clear saved history" }).click();
  await page.getByRole("button", { name: /0 saved/i }).waitFor();
  await page.getByRole("button", { name: /reset/i }).click();
  await waitForApiState((state) => state.status === "idle");

  const disconnectedPage = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  let interceptedSocketCount = 0;
  await disconnectedPage.routeWebSocket(/\/ws\/live$/, (webSocket) => {
    interceptedSocketCount += 1;
    webSocket.close({ code: 1011, reason: "Intentional reconnect-button check" });
  });
  await disconnectedPage.goto(baseUrl, { waitUntil: "domcontentloaded" });
  await disconnectedPage.getByRole("button", { name: "Reconnect" }).waitFor({ timeout: 15000 });
  const reloaded = new Promise((resolve) => disconnectedPage.once("framenavigated", resolve));
  await disconnectedPage.getByRole("button", { name: "Reconnect" }).click();
  await reloaded;
  if (interceptedSocketCount < 1 || !disconnectedPage.url().startsWith(baseUrl)) throw new Error("Reconnect button did not reload the dashboard after a WebSocket disconnect");
  await disconnectedPage.close();
  console.log(JSON.stringify({
    status: await page.locator(".connection-pill").textContent(),
    simulationTime: await page.locator(".clock-label b").first().textContent(),
    activeSceneCount: await page.locator(".scene-grid canvas").count(),
    emptySceneLabels: await page.locator(".scene-empty:visible").count(),
    vehicleTypes: [...new Set(adaptiveVehicles.map((vehicle) => vehicle.type_id))].sort(),
    vehiclePositionSample: adaptiveVehicles.slice(0, 3).map(({ vehicle_id, type_id, x_m, y_m }) => ({ vehicle_id, type_id, x_m, y_m })),
    screenshots: ["dashboard-1440x900.png", "dashboard-1920x1080.png", "dashboard-live-insights.png"],
    pauseResumeStopValidated: true,
    durationInputValidated: true,
    quickDemoValidated: true,
    singleModeQueuesValidated: true,
    liveDashboardModulesValidated: true,
    liveDetectorRates: detectorRates,
    performanceReportValidated: true,
    qualityTiersAndDynamicResolutionToggleValidated: true,
    synchronizedCameraPresetsValidated: true,
    performanceReportFile: performanceDownload.suggestedFilename(),
    downloadButtonsValidated: downloadedFiles.map(({ name, bytes }) => ({ name, bytes })),
    resetValidated: true,
    errorDismissValidated: true,
    apiDocsLinkValidated: true,
    historySelectExportClearValidated: true,
    reconnectValidated: true,
    csvExportButtons: csvButtons,
    jsonExportButtons: jsonButtons,
    errors,
    expectedErrors,
  }, null, 2));
  if (errors.length) process.exitCode = 1;
} finally {
  try { await page.getByRole("button", { name: /stop/i }).click({ timeout: 1000 }); } catch {}
  await browser.close();
}
