const form = document.querySelector("#run-form");
const runButton = document.querySelector("#run-button");
const messageInput = document.querySelector("#incident-message");
const modeButtons = [...document.querySelectorAll(".mode-button")];
const resultPlaceholder = document.querySelector("#result-placeholder");
const resultContent = document.querySelector("#result-content");
const apiStatus = document.querySelector("#api-status");

let selectedMode = "normal";
let currentRun = null;

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function label(value) {
  return String(value ?? "—").replaceAll("_", " ");
}

function setMode(mode) {
  selectedMode = mode;
  for (const button of modeButtons) {
    const active = button.dataset.mode === mode;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  }
}

function setBusy(busy) {
  runButton.disabled = busy;
  runButton.classList.toggle("busy", busy);
  runButton.querySelector("span").textContent = busy ? "正在生成证据链" : "运行协作链路";
  if (busy) {
    resultContent.classList.add("hidden");
    resultPlaceholder.classList.remove("hidden");
    resultPlaceholder.classList.add("loading");
    resultPlaceholder.querySelector("h2").textContent = "Agent 协作进行中";
    resultPlaceholder.querySelector("p").textContent = "正在规范化、取证、诊断、执行并重新验证业务状态。";
  }
}

function renderAgentTrack(trace) {
  const completedAgents = new Set(trace.map((event) => event.agent));
  for (const node of document.querySelectorAll("#agent-track li")) {
    node.classList.toggle("complete", completedAgents.has(node.dataset.agent));
  }
}

function renderObservations(context) {
  const observations = [
    ["IAM account", context.account.locked ? "locked" : "unlocked", context.account.locked ? "warn" : "ok"],
    ["Lock reason", context.account.lock_reason, "neutral"],
    ["VPN", context.vpn.enabled ? "enabled" : "disabled", context.vpn.enabled ? "ok" : "warn"],
    ["Docs permission", context.permission.granted ? "granted" : "missing", context.permission.granted ? "ok" : "warn"],
    ["Service health", context.service.status, context.service.status === "HEALTHY" ? "ok" : "warn"],
    ["Initial access", context.access_probe.accessible ? "accessible" : "inaccessible", context.access_probe.accessible ? "ok" : "warn"]
  ];
  document.querySelector("#observation-list").innerHTML = observations.map(([name, value, status]) => `
    <div>
      <span>${escapeHtml(name)}</span>
      <strong class="value-${status}"><i></i>${escapeHtml(label(value))}</strong>
    </div>
  `).join("");
}

function renderAssertions(verification) {
  document.querySelector("#assertion-list").innerHTML = verification.assertions.map((assertion) => `
    <div class="assertion ${assertion.passed ? "pass" : "fail"}">
      <span class="assertion-icon">${assertion.passed ? "✓" : "!"}</span>
      <div>
        <strong>${escapeHtml(label(assertion.assertion_id))}</strong>
        <small>expected ${escapeHtml(assertion.expected)} · observed ${escapeHtml(assertion.actual)}</small>
      </div>
      <b>${assertion.passed ? "PASS" : "FAIL"}</b>
    </div>
  `).join("");
}

function renderTrace(trace) {
  const important = trace.filter((event) => [
    "run_started",
    "task_delegated",
    "artifact_created",
    "policy_evaluated",
    "tool_call",
    "verification_completed",
    "run_finished"
  ].includes(event.event_type));
  document.querySelector("#trace-count").textContent = `${trace.length} events`;
  document.querySelector("#trace-list").innerHTML = important.map((event) => `
    <li>
      <span class="trace-dot"></span>
      <div class="trace-meta">
        <strong>${escapeHtml(label(event.event_type))}</strong>
        <span>${escapeHtml(event.agent)} · ${escapeHtml(label(event.stage))}</span>
      </div>
      <time>${escapeHtml(event.occurred_at.slice(11, 19))}</time>
    </li>
  `).join("");
}

function renderArtifact(name) {
  if (!currentRun) return;
  for (const button of document.querySelectorAll("#artifact-tabs button")) {
    const active = button.dataset.artifact === name;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
  }
  const value = name === "result" ? currentRun.result : currentRun.artifacts[name];
  document.querySelector("#artifact-json code").textContent = JSON.stringify(value, null, 2);
}

function renderArtifactTabs(run) {
  const preferred = ["result", "diagnosis", "policy_decision", "execution", "verification", "tool_calls", "trace"];
  const container = document.querySelector("#artifact-tabs");
  container.innerHTML = preferred.map((name) => `
    <button type="button" role="tab" data-artifact="${name}">${escapeHtml(label(name))}</button>
  `).join("");
  for (const button of container.querySelectorAll("button")) {
    button.addEventListener("click", () => renderArtifact(button.dataset.artifact));
  }
  renderArtifact("result");
}

function renderRun(payload) {
  currentRun = payload;
  const { result, artifacts } = payload;
  const completed = result.status === "COMPLETED";

  resultPlaceholder.classList.add("hidden");
  resultPlaceholder.classList.remove("loading");
  resultContent.classList.remove("hidden");
  resultContent.classList.toggle("failed", !completed);

  document.querySelector("#result-title").textContent = completed ? "业务访问已恢复" : "拒绝误关单";
  document.querySelector("#result-message").textContent = result.message;
  document.querySelector("#run-id").textContent = result.run_id;
  document.querySelector("#metric-task").textContent = label(result.status);
  document.querySelector("#metric-root").textContent = label(result.root_cause);
  document.querySelector("#metric-tool").textContent = label(result.tool_status);
  document.querySelector("#metric-verify").textContent = label(result.verification_status);
  document.querySelector("#metric-task").className = completed ? "metric-ok" : "metric-fail";
  document.querySelector("#metric-verify").className = completed ? "metric-ok" : "metric-fail";
  document.querySelector("#evidence-count").textContent = `${artifacts.evidence.length} evidence`;
  document.querySelector("#truth-tool").textContent = result.tool_status;
  document.querySelector("#truth-task").textContent = result.status;
  document.querySelector("#truth-task").className = completed ? "truth-ok" : "truth-fail";

  renderAgentTrack(artifacts.trace);
  renderObservations(artifacts.context);
  renderAssertions(artifacts.verification);
  renderTrace(artifacts.trace);
  renderArtifactTabs(payload);
}

async function runDemo() {
  setBusy(true);
  try {
    const response = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: messageInput.value, mode: selectedMode })
    });
    const payload = await response.json();
    if (!response.ok || !payload.ok) {
      throw new Error(payload.message ?? payload.error ?? "Demo request failed");
    }
    renderRun(payload);
  } catch (error) {
    resultPlaceholder.classList.remove("loading");
    resultPlaceholder.querySelector("h2").textContent = "运行失败";
    resultPlaceholder.querySelector("p").textContent = error.message;
  } finally {
    setBusy(false);
  }
}

async function checkHealth() {
  try {
    const response = await fetch("/api/health");
    if (!response.ok) throw new Error("offline");
    apiStatus.classList.add("online");
    apiStatus.innerHTML = "<i></i> SANDBOX ONLINE";
  } catch {
    apiStatus.classList.add("offline");
    apiStatus.innerHTML = "<i></i> API OFFLINE";
  }
}

for (const button of modeButtons) {
  button.addEventListener("click", () => setMode(button.dataset.mode));
}
form.addEventListener("submit", (event) => {
  event.preventDefault();
  runDemo();
});

setMode("normal");
checkHealth();

