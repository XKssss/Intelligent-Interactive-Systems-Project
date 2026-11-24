// RepairAgent single-page interface.
const sceneEl = document.getElementById("scene");
const chatEl = document.getElementById("chat");
const understandingEl = document.getElementById("understanding");
const repairLogEl = document.getElementById("repair-log");
const chipEl = document.getElementById("deictic-chip");
const utteranceEl = document.getElementById("utterance");
const statusPill = document.getElementById("status-pill");
const boundaryText = document.getElementById("boundary-text");

let pendingDeictic = null;            // {target_id, modality}
let deicticModality = "point";        // toggle between point and gaze
let awaitingClarification = false;
let blockLabels = {};

// ------------------------------------------------------------------ API
async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  return response.json();
}

async function loadState() {
  const state = await api("/api/state");
  blockLabels = Object.fromEntries(
    state.blocks.map((b) => [b.id, `${b.size} ${b.color} ${b.shape}`]));
  renderScene(state);
}

// ------------------------------------------------------------ scene rendering
function renderScene(state) {
  sceneEl.innerHTML = "";
  for (const block of state.blocks) {
    const el = document.createElement("div");
    el.className = `block ${block.shape}${state.selected_id === block.id ? " selected" : ""}`;
    el.style.left = `${block.x}px`;
    el.style.top = `${block.y}px`;
    el.title = `${block.id}: ${block.size} ${block.color} ${block.shape}`;
    el.dataset.id = block.id;
    el.textContent = block.id;
    const tag = document.createElement("span");
    tag.className = "tag";
    tag.textContent = block.label;
    el.appendChild(tag);
    el.addEventListener("click", () => onBlockClick(block.id));
    sceneEl.appendChild(el);
  }
}

function onBlockClick(id) {
  if (awaitingClarification) {
    sendTurn({ deictic_target: id, deictic_modality: deicticModality });
    return;
  }
  pendingDeictic = { target_id: id, modality: deicticModality };
  renderChip();
}

function renderChip() {
  if (!pendingDeictic) {
    chipEl.classList.add("hidden");
    return;
  }
  chipEl.classList.remove("hidden");
  chipEl.innerHTML =
    `<span>${pendingDeictic.modality === "gaze" ? "Gaze at" : "Pointing at"}:
      <strong>${pendingDeictic.target_id} (${blockLabels[pendingDeictic.target_id]})</strong></span>
     <button type="button" id="clear-chip">clear</button>`;
  document.getElementById("clear-chip").addEventListener("click", () => {
    pendingDeictic = null;
    renderChip();
  });
}

// --------------------------------------------------------------- turn handling
async function sendTurn(extra = {}) {
  const payload = { utterance: utteranceEl.value.trim(), ...extra };
  if (pendingDeictic && !payload.deictic_target) {
    payload.deictic_target = pendingDeictic.target_id;
    payload.deictic_modality = pendingDeictic.modality;
  }
  if (!payload.utterance && !payload.deictic_target) return;

  appendUserMessage(payload);
  utteranceEl.value = "";
  pendingDeictic = null;
  renderChip();
  statusPill.textContent = "Thinking";

  const response = await api("/api/turn", { method: "POST", body: JSON.stringify(payload) });
  if (response.error) {
    appendMessage("agent", "System", response.error);
    statusPill.textContent = "Ready";
    return;
  }
  handleResponse(response);
}

function handleResponse(response) {
  awaitingClarification = response.decision.kind === "clarify";
  statusPill.textContent = awaitingClarification ? "Clarification needed" : "Ready";
  appendMessage(
    awaitingClarification ? "clarify" : "agent",
    "Agent",
    response.feedback,
    response.channels,
  );
  updateUnderstanding(response);
  updateRepairLog(response.repair_log);
  renderScene(response.state);
  if (response.autonomy_boundary) boundaryText.textContent = response.autonomy_boundary;
}

function appendUserMessage(payload) {
  const parts = [];
  if (payload.utterance) parts.push(payload.utterance);
  if (payload.deictic_target) {
    parts.push(`${payload.deictic_modality === "gaze" ? "gaze at" : "point at"} ${payload.deictic_target}`);
  }
  const tags = [];
  if (payload.utterance) tags.push("speech");
  if (payload.deictic_target) tags.push(payload.deictic_modality);
  appendMessage("user", "You", parts.join(" &mdash; "), tags, true);
}

function appendMessage(kind, who, text, tags = [], isHtml = false) {
  const el = document.createElement("div");
  el.className = `msg ${kind}`;
  const whoTag = document.createElement("span");
  whoTag.className = "who";
  whoTag.textContent = who;
  el.appendChild(whoTag);
  const body = document.createElement("span");
  if (isHtml) body.innerHTML = text; else body.textContent = text;
  el.appendChild(body);
  if (tags.length) {
    const wrap = document.createElement("div");
    wrap.className = "chips";
    for (const tag of tags) {
      const chip = document.createElement("span");
      chip.className = "channel-tag";
      chip.textContent = tag;
      wrap.appendChild(chip);
    }
    el.appendChild(wrap);
  }
  chatEl.appendChild(el);
  chatEl.scrollTop = chatEl.scrollHeight;
}

// --------------------------------------------------------- understanding panel
function updateUnderstanding(response) {
  const parse = response.parse;
  const attrs = Object.entries(parse.attributes)
    .filter(([, v]) => v !== null)
    .map(([k, v]) => `${k}: ${v}`)
    .join(", ") || "none";
  const actionText = response.action.message || "no action";
  const confidencePct = Math.round(parse.confidence * 100);

  understandingEl.innerHTML = `
    <dl class="kv">
      <dt>Intent</dt><dd>${parse.intent}</dd>
      <dt>Attributes</dt><dd>${attrs}</dd>
      <dt>Confidence</dt><dd>${confidencePct}%
        <div class="confidence-track"><div class="confidence-fill" style="width:${confidencePct}%"></div></div></dd>
      <dt>Channels</dt><dd>${response.channels.join(", ") || "none"}</dd>
      <dt>Candidates</dt><dd>${response.decision.candidates.join(", ") || "none"}</dd>
      <dt>Decision</dt><dd>${response.decision.kind}</dd>
      <dt>Action</dt><dd>${actionText}</dd>
    </dl>`;
}

function updateRepairLog(log) {
  repairLogEl.innerHTML = "";
  for (const entry of log) {
    const li = document.createElement("li");
    li.textContent = `${entry.repair_type} &rarr; ${entry.resolution}`;
    li.innerHTML = `${entry.repair_type} &rarr; ${entry.resolution}`;
    repairLogEl.appendChild(li);
  }
}

// ------------------------------------------------------------ voice input
const micBtn = document.getElementById("btn-mic");
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SpeechRecognition) {
  const recognition = new SpeechRecognition();
  recognition.lang = "en-GB";
  recognition.interimResults = false;
  recognition.onresult = (event) => {
    utteranceEl.value = event.results[0][0].transcript;
  };
  recognition.onend = () => micBtn.classList.remove("listening");
  micBtn.addEventListener("click", () => {
    micBtn.classList.add("listening");
    recognition.start();
  });
} else {
  micBtn.disabled = true;
  micBtn.title = "Speech recognition not supported in this browser";
}

// ------------------------------------------------------------ controls
document.getElementById("btn-send").addEventListener("click", () => sendTurn());
utteranceEl.addEventListener("keydown", (event) => {
  if (event.key === "Enter") sendTurn();
});

document.getElementById("mode-point").addEventListener("click", () => {
  deicticModality = "point";
  document.getElementById("mode-point").classList.add("active");
  document.getElementById("mode-gaze").classList.remove("active");
});
document.getElementById("mode-gaze").addEventListener("click", () => {
  deicticModality = "gaze";
  document.getElementById("mode-gaze").classList.add("active");
  document.getElementById("mode-point").classList.remove("active");
});

document.getElementById("btn-reset").addEventListener("click", async () => {
  await api("/api/reset", { method: "POST" });
  chatEl.innerHTML = "";
  repairLogEl.innerHTML = "";
  understandingEl.innerHTML =
    '<p class="muted">No interpretation yet. Send a command to see what the agent senses and infers.</p>';
  awaitingClarification = false;
  pendingDeictic = null;
  renderChip();
  statusPill.textContent = "Ready";
  loadState();
});

document.getElementById("btn-transcript").addEventListener("click", async () => {
  const data = await api("/api/transcript");
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "repair_agent_transcript.json";
  link.click();
  URL.revokeObjectURL(url);
});

loadState();
