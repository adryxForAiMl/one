import { existsSync } from "node:fs";
import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { chromium } from "playwright";

const webUrl = process.env.TRAFFIC_WEB_URL ?? "http://127.0.0.1:5173";
const outputDir = resolve(process.env.TRAFFIC_DYNAMIC_RESOLUTION_DIR ?? "../docs/visual/dynamic-resolution");
const defaultBrowser = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser";
const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ?? (existsSync(defaultBrowser) ? defaultBrowser : undefined);
await mkdir(outputDir, { recursive: true });
const browser = await chromium.launch({ headless: true, ...(executablePath ? { executablePath } : {}) });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
page.on("console", (message) => { if (message.type() === "error") errors.push(message.text()); });

try {
  await page.goto(webUrl, { waitUntil: "networkidle" });
  await page.waitForFunction(() => Boolean(window.__trafficSceneDiagnostics?.["Fixed-time"]?.()));
  const automaticResolution = page.getByLabel("Automatic resolution");
  await automaticResolution.waitFor({ state: "attached" });
  if (!(await automaticResolution.isChecked())) throw new Error("Automatic resolution is disabled");
  const initial = await page.evaluate(() => window.__trafficSceneDiagnostics?.["Fixed-time"]?.()?.viewport.resolutionScale ?? null);
  if (initial !== 1) throw new Error(`Expected initial resolution scale 1, received ${initial}`);

  await page.evaluate(() => {
    window.__trafficResolutionStressTimer = window.setInterval(() => {
      const start = performance.now();
      while (performance.now() - start < 24) { /* Deliberate main-thread pressure for governor QA. */ }
    }, 30);
  });
  await page.waitForFunction(() => {
    const scale = window.__trafficSceneDiagnostics?.["Fixed-time"]?.()?.viewport.resolutionScale;
    return typeof scale === "number" && scale < 1;
  }, null, { timeout: 15000 });
  const reduced = await page.evaluate(() => window.__trafficSceneDiagnostics?.["Fixed-time"]?.()?.viewport.resolutionScale ?? null);
  await page.screenshot({ path: resolve(outputDir, "resolution-reduced.png") });
  await page.evaluate(() => window.clearInterval(window.__trafficResolutionStressTimer));
  await page.waitForFunction((previousScale) => {
    const scale = window.__trafficSceneDiagnostics?.["Fixed-time"]?.()?.viewport.resolutionScale;
    return typeof scale === "number" && scale > previousScale;
  }, reduced, { timeout: 20000 });
  const restored = await page.evaluate(() => window.__trafficSceneDiagnostics?.["Fixed-time"]?.()?.viewport.resolutionScale ?? null);
  const report = {
    captured_at: new Date().toISOString(),
    test: "controlled main-thread frame pressure followed by recovery",
    initial_scale: initial,
    minimum_observed_scale: reduced,
    scale_after_recovery: restored,
    expected_behavior: "reduce device pixel ratio after sustained frame intervals above 18.2 ms, restore gradually after stable intervals below 16.9 ms",
    errors,
  };
  await writeFile(resolve(outputDir, "dynamic-resolution-report.json"), `${JSON.stringify(report, null, 2)}\n`);
  console.log(JSON.stringify(report, null, 2));
  if (errors.length) process.exitCode = 1;
} finally {
  await browser.close();
}
