import { chromium } from "playwright";

const pageUrl = process.env.TRAFFIC_WEB_URL ?? "http://127.0.0.1:5173";
const apiUrl = process.env.TRAFFIC_API_URL ?? "http://127.0.0.1:8000";
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 2560, height: 1440 }, deviceScaleFactor: 1 });

try {
  await page.goto(pageUrl, { waitUntil: "networkidle" });
  await page.waitForFunction(() => document.querySelector(".panel-bottom")?.textContent?.includes("API reachable"));
  await page.evaluate(async (url) => {
    const response = await fetch(`${url}/api/simulation/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mode: "compare", scenario: "balanced", seed: 42, duration_seconds: 3600,
        north_south_veh_per_hour: 7200, east_west_veh_per_hour: 7200,
      }),
    });
    if (!response.ok) throw new Error(`Could not start load run: ${await response.text()}`);
  }, apiUrl);
  await page.waitForFunction(async (url) => {
    const state = await fetch(`${url}/api/state`, { cache: "no-store" }).then((response) => response.json());
    return (state.controllers.fixed?.vehicles.length ?? 0) >= 100 &&
      (state.controllers.adaptive?.vehicles.length ?? 0) >= 100;
  }, apiUrl, { timeout: 120000, polling: 250 });
  const measurements = [];
  for (const quality of ["high", "medium", "low"]) {
    await page.locator("#quality").selectOption(quality);
    await page.waitForTimeout(800);
    const framesPerSecond = await page.evaluate(() => new Promise((resolve) => {
      let frames = 0;
      const started = performance.now();
      const tick = (now) => {
        frames += 1;
        if (now - started >= 2000) resolve((frames * 1000) / (now - started));
        else requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    }));
    measurements.push({ quality, browserAnimationFrameRate: Number(framesPerSecond.toFixed(1)) });
  }
  const state = await page.evaluate(async (url) => fetch(`${url}/api/state`, { cache: "no-store" }).then((response) => response.json()), apiUrl);
  console.log(JSON.stringify({
    viewport: "2560x1440",
    fixedVehicles: state.controllers.fixed.vehicles.length,
    adaptiveVehicles: state.controllers.adaptive.vehicles.length,
    measurements,
    note: "Headless Chromium animation-frame measurement; not a MacBook Air GPU benchmark.",
  }, null, 2));
} finally {
  try {
    await page.evaluate(async (url) => fetch(`${url}/api/simulation/stop`, { method: "POST" }), apiUrl);
  } catch {}
  await browser.close();
}
