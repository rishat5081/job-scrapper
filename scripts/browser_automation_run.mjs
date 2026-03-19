import fs from "node:fs/promises";

const targetWsUrl = process.env.CDP_TARGET_WS_URL;
const browserWsUrl = process.env.CDP_BROWSER_WS_URL;
const targetPageUrl = process.env.CDP_TARGET_URL || "http://127.0.0.1:8080/?automation=1&no_pdf_preview=1";
const screenshotPath = process.env.AUTOMATION_SCREENSHOT_PATH || "/tmp/jobs_dashboard_automation_cdp.png";
const domPath = process.env.AUTOMATION_DOM_PATH || "/tmp/jobs_dashboard_automation_cdp.html";
const resultPath = process.env.AUTOMATION_RESULT_PATH || "/tmp/jobs_dashboard_automation_result.json";
const timeoutMs = Number(process.env.AUTOMATION_TIMEOUT_MS || 120000);

if (!targetWsUrl && !browserWsUrl) {
  console.error("CDP_TARGET_WS_URL or CDP_BROWSER_WS_URL is required.");
  process.exit(1);
}

const ws = new WebSocket(targetWsUrl || browserWsUrl);
let nextId = 1;
const pending = new Map();
let sessionId = null;

function send(method, params = {}, options = {}) {
  const id = nextId += 1;
  const payload = { id, method, params };
  if (options.sessionId) {
    payload.sessionId = options.sessionId;
  }
  ws.send(JSON.stringify(payload));
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject, method });
  });
}

function parseValue(response) {
  const value = response?.result?.result?.value;
  if (typeof value !== "string") {
    throw new Error("Expected string response from Runtime.evaluate");
  }
  return JSON.parse(value);
}

async function evaluate(expression) {
  const response = await send("Runtime.evaluate", {
    expression,
    returnByValue: true,
    awaitPromise: true,
  }, sessionId ? { sessionId } : {});
  if (response.result?.exceptionDetails) {
    throw new Error(`Runtime.evaluate failed: ${JSON.stringify(response.result.exceptionDetails)}`);
  }
  return response;
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

ws.onmessage = event => {
  const message = JSON.parse(event.data);
  if (!message.id) {
    return;
  }
  const entry = pending.get(message.id);
  if (!entry) {
    return;
  }
  pending.delete(message.id);
  if (message.error) {
    entry.reject(new Error(`${entry.method}: ${message.error.message}`));
    return;
  }
  entry.resolve(message);
};

ws.onerror = error => {
  console.error("WebSocket error:", error.message || String(error));
};

async function run() {
  await new Promise((resolve, reject) => {
    ws.onopen = resolve;
    ws.onclose = () => reject(new Error("CDP socket closed before automation completed"));
  });

  if (browserWsUrl) {
    const targetsResponse = await send("Target.getTargets");
    const targets = targetsResponse.result.targetInfos || [];
    const target = targets.find(item => item.type === "page" && item.url === targetPageUrl);
    if (!target) {
      throw new Error(`Target page not found for ${targetPageUrl}`);
    }
    const attachResponse = await send("Target.attachToTarget", {
      targetId: target.targetId,
      flatten: true,
    });
    sessionId = attachResponse.result.sessionId;
  }

  await send("Page.enable", {}, sessionId ? { sessionId } : {});
  await send("Runtime.enable", {}, sessionId ? { sessionId } : {});

  const startedAt = Date.now();
  let state = null;

  while (Date.now() - startedAt < timeoutMs) {
    const response = await evaluate(`(() => JSON.stringify({
      readyState: document.readyState,
      automationComplete: document.body.dataset.automationComplete || "",
      status: document.getElementById("statusLine")?.textContent?.trim() || "",
      automationResult: document.getElementById("automationResult")?.textContent || "",
      artifactCount: document.querySelectorAll("#artifactsPanel .artifact-card").length,
      jobCount: document.querySelectorAll("#jobs .job-card").length,
      previewState: document.querySelector("#previewBody iframe") ? "iframe" : (document.querySelector("#previewBody .preview-empty") ? "placeholder" : "empty")
    }))()`);
    state = parseValue(response);
    if (state.automationComplete === "true" || state.automationComplete === "error") {
      break;
    }
    await sleep(1000);
  }

  if (!state || (state.automationComplete !== "true" && state.automationComplete !== "error")) {
    throw new Error(`Timed out waiting for dashboard automation completion. Last state: ${JSON.stringify(state)}`);
  }

  const domResponse = await evaluate("document.documentElement.outerHTML");
  const domHtml = domResponse.result.result.value || "";

  const screenshot = await send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: true,
  }, sessionId ? { sessionId } : {});

  const payload = {
    completedAt: new Date().toISOString(),
    state,
  };

  await fs.writeFile(screenshotPath, Buffer.from(screenshot.result.data, "base64"));
  await fs.writeFile(domPath, domHtml, "utf8");
  await fs.writeFile(resultPath, JSON.stringify(payload, null, 2), "utf8");

  await send("Browser.close").catch(() => {});
}

run()
  .then(() => {
    process.exit(0);
  })
  .catch(async error => {
    const payload = {
      completedAt: new Date().toISOString(),
      error: error.message,
    };
    await fs.writeFile(resultPath, JSON.stringify(payload, null, 2), "utf8").catch(() => {});
    console.error(error.message);
    process.exit(1);
  });
