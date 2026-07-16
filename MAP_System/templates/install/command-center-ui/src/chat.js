const feed = document.getElementById("feed");
const input = document.getElementById("input");
const composer = document.getElementById("composer");
const sendBtn = document.getElementById("send");
const presenceList = document.getElementById("presence-list");
const presenceCount = document.getElementById("presence-count");
const usageRefreshBtn = document.getElementById("usage-refresh");
const usageRefreshState = document.getElementById("usage-refresh-state");
const mapSummary = document.getElementById("map-summary");
const mapHealthOverall = document.getElementById("map-health-overall");
const mapHealthRows = document.getElementById("map-health-rows");
const labSectionState = document.getElementById("lab-section-state");
const connStatus = document.getElementById("conn-status");
const mentionHint = document.getElementById("mention-hint");
const labBanner = document.getElementById("lab-banner");
const labBannerText = document.getElementById("lab-banner-text");
const labStartBtn = document.getElementById("lab-start");
const projectUpdaterCard = document.getElementById("project-updater-card");
const projectUpdaterState = document.getElementById("project-updater-state");
const projectUpdaterSummary = document.getElementById("project-updater-summary");
const projectUpdaterCount = document.getElementById("project-updater-count");
const projectUpdaterProjects = document.getElementById("project-updater-projects");
const projectUpdaterOpen = document.getElementById("project-updater-open");
const projectUpdaterModalOpen = document.getElementById("project-updater-modal-open");
const projectUpdaterModal = document.getElementById("project-updater-modal");
const projectUpdaterModalClose = document.getElementById("project-updater-modal-close");
const projectUpdaterFrame = document.getElementById("project-updater-frame");
const projectUpdaterModalNote = document.getElementById("project-updater-modal-note");
const timerCount = document.getElementById("timer-count");
const timerNow = document.getElementById("timer-now");
const timerNext = document.getElementById("timer-next");
const timerModeCountdown = document.getElementById("timer-mode-countdown");
const timerModeAlarm = document.getElementById("timer-mode-alarm");
const timerForm = document.getElementById("timer-form");
const timerLabel = document.getElementById("timer-label");
const timerValue = document.getElementById("timer-value");
const timerList = document.getElementById("timer-list");
const screenPanel = document.getElementById("screen-panel");
const screenTitle = document.getElementById("screen-title");
const screenBody = document.getElementById("screen-body");
const screenForm = document.getElementById("screen-form");
const screenInput = document.getElementById("screen-input");
const screenEnterBtn = document.getElementById("screen-enter");
const screenCloseBtn = document.getElementById("screen-close");

let screenAgent = null;
let screenTimer = null;

const bubbles = new Map(); // event id -> {bubble, msg}
const nodes = new Map(); // event id -> message DOM node (for jump-to)
let gistsEnabled = localStorage.getItem("gists") !== "off";

const attentionHead = document.getElementById("attention-head");
const attentionCount = document.getElementById("attention-count");
const attentionList = document.getElementById("attention-list");
const replyChip = document.getElementById("reply-chip");
const replyChipSender = document.getElementById("reply-chip-sender");
const replyChipText = document.getElementById("reply-chip-text");
const replyCancelBtn = document.getElementById("reply-cancel");
let replyTarget = null; // {id, sender, text}

function startReply(target) {
  replyTarget = target;
  replyChipSender.textContent = `↩ ${target.sender}`;
  replyChipText.textContent = target.text.slice(0, 120);
  replyChip.hidden = false;
  input.focus();
}

function cancelReply() {
  replyTarget = null;
  replyChip.hidden = true;
}

replyCancelBtn.addEventListener("click", cancelReply);

let lastId = 0;
let operator = "command-center";
let knownAgents = [];
let lastDay = "";
let hintIndex = 0;
let projectUpdaterEmbeddedUrl = "/project-updater/";
let pendingProjectSearch = "";
let providerUsage = {};

const MENTION_RE = /(?<![\w@])@([A-Za-z0-9_-]{2,64})/g;
const PROJECT_UPDATER_STORE_KEY = "projectUpdater.v1";
const TIMER_STORE_KEY = "commandCenterTimers.v1";
const DAY_MS = 24 * 60 * 60 * 1000;
let timerMode = "countdown";
let timers = loadTimers();
let audioContext = null;
let chimeTimer = null;
let previousTitle = document.title;

document.querySelectorAll(".sidebar-section-head").forEach((button) => {
  const section = button.closest(".sidebar-section");
  const storageKey = `sidebar:${section.dataset.sidebarSection}:collapsed`;
  const collapsed = localStorage.getItem(storageKey) === "1";
  section.classList.toggle("collapsed", collapsed);
  button.setAttribute("aria-expanded", String(!collapsed));
  button.addEventListener("click", () => {
    const next = !section.classList.contains("collapsed");
    section.classList.toggle("collapsed", next);
    button.setAttribute("aria-expanded", String(!next));
    localStorage.setItem(storageKey, next ? "1" : "0");
  });
});

function loadTimers() {
  try {
    const raw = JSON.parse(localStorage.getItem(TIMER_STORE_KEY) || "[]");
    if (!Array.isArray(raw)) return [];
    return raw
      .filter((timer) => timer && typeof timer.targetAt === "number" && timer.targetAt > 0)
      .map((timer) => ({
        id: String(timer.id || crypto.randomUUID()),
        type: timer.type === "alarm" ? "alarm" : "countdown",
        label: String(timer.label || ""),
        targetAt: Number(timer.targetAt),
        ringing: Boolean(timer.ringing),
      }));
  } catch {
    return [];
  }
}

function saveTimers() {
  localStorage.setItem(TIMER_STORE_KEY, JSON.stringify(timers));
}

function setTimerMode(mode) {
  timerMode = mode === "alarm" ? "alarm" : "countdown";
  timerModeCountdown.classList.toggle("selected", timerMode === "countdown");
  timerModeAlarm.classList.toggle("selected", timerMode === "alarm");
  timerValue.placeholder = timerMode === "alarm" ? "700 or 14:30" : "10m or 1h 30m";
}

function parseAlarmTime(value) {
  const cleaned = value.trim().replace(/\s+/g, "");
  if (!cleaned) throw new Error("Enter a time.");
  let hour;
  let minute;
  if (cleaned.includes(":")) {
    const parts = cleaned.split(":");
    if (parts.length !== 2 || !parts.every((part) => /^\d+$/.test(part))) {
      throw new Error("Use 700, 1305, 7:30, or 13:05.");
    }
    hour = Number(parts[0]);
    minute = Number(parts[1]);
  } else {
    if (!/^\d+$/.test(cleaned)) throw new Error("Use numbers only, with an optional colon.");
    if (cleaned.length <= 2) {
      hour = Number(cleaned);
      minute = 0;
    } else if (cleaned.length === 3) {
      hour = Number(cleaned.slice(0, 1));
      minute = Number(cleaned.slice(1));
    } else if (cleaned.length === 4) {
      hour = Number(cleaned.slice(0, 2));
      minute = Number(cleaned.slice(2));
    } else {
      throw new Error("Use 700, 1305, 7:30, or 13:05.");
    }
  }
  if (hour < 0 || hour > 23) throw new Error("The hour must be between 0 and 23.");
  if (minute < 0 || minute > 59) throw new Error("The minutes must be between 00 and 59.");
  const target = new Date();
  target.setHours(hour, minute, 0, 0);
  if (target.getTime() <= Date.now()) target.setDate(target.getDate() + 1);
  return target.getTime();
}

function parseCountdown(value) {
  const text = value.trim().toLowerCase();
  if (!text) throw new Error("Enter a timer length.");
  let seconds = 0;
  const unitMatches = [...text.matchAll(/(\d+(?:\.\d+)?)\s*(h|hr|hrs|hour|hours|m|min|mins|minute|minutes|s|sec|secs|second|seconds)\b/g)];
  if (unitMatches.length) {
    for (const match of unitMatches) {
      const amount = Number(match[1]);
      const unit = match[2][0];
      if (unit === "h") seconds += amount * 3600;
      else if (unit === "m") seconds += amount * 60;
      else seconds += amount;
    }
  } else if (/^\d+:\d{1,2}(?::\d{1,2})?$/.test(text)) {
    const parts = text.split(":").map(Number);
    if (parts.length === 2) seconds = parts[0] * 60 + parts[1];
    else seconds = parts[0] * 3600 + parts[1] * 60 + parts[2];
  } else if (/^\d+(?:\.\d+)?$/.test(text)) {
    seconds = Number(text) * 60;
  } else {
    throw new Error("Use 10m, 1h 30m, 90, or 05:00.");
  }
  seconds = Math.round(seconds);
  if (seconds <= 0) throw new Error("Timer must be longer than zero.");
  if (seconds > 7 * 24 * 3600) throw new Error("Timer must be under seven days.");
  return Date.now() + seconds * 1000;
}

function formatDuration(ms) {
  const total = Math.max(0, Math.ceil(ms / 1000));
  const days = Math.floor(total / 86400);
  let remainder = total % 86400;
  const hours = Math.floor(remainder / 3600);
  remainder %= 3600;
  const minutes = Math.floor(remainder / 60);
  const seconds = remainder % 60;
  if (days) return `${days}d ${hours.toString().padStart(2, "0")}h ${minutes.toString().padStart(2, "0")}m`;
  if (hours) return `${hours.toString().padStart(2, "0")}h ${minutes.toString().padStart(2, "0")}m ${seconds.toString().padStart(2, "0")}s`;
  return `${minutes.toString().padStart(2, "0")}m ${seconds.toString().padStart(2, "0")}s`;
}

function formatHeaderDuration(ms) {
  const total = Math.max(0, Math.ceil(ms / 1000));
  const days = Math.floor(total / 86400);
  let remainder = total % 86400;
  const hours = Math.floor(remainder / 3600);
  remainder %= 3600;
  const minutes = Math.floor(remainder / 60);
  const seconds = remainder % 60;
  if (days) return `${days}d ${hours}h`;
  if (hours) return `${hours}h ${minutes.toString().padStart(2, "0")}m`;
  return `${minutes.toString().padStart(2, "0")}m ${seconds.toString().padStart(2, "0")}s`;
}

function timerTitle(timer) {
  if (timer.label) return timer.label;
  return timer.type === "alarm" ? "Alarm" : "Timer";
}

function ensureAudio() {
  const AudioCtx = window.AudioContext || window.webkitAudioContext;
  if (!AudioCtx) return null;
  if (!audioContext) audioContext = new AudioCtx();
  if (audioContext.state === "suspended") audioContext.resume();
  return audioContext;
}

function playChime() {
  const ctx = ensureAudio();
  if (!ctx) return;
  const now = ctx.currentTime;
  [
    { frequency: 392.0, delay: 0.0, peak: 0.035 },
    { frequency: 493.88, delay: 0.32, peak: 0.03 },
    { frequency: 587.33, delay: 0.66, peak: 0.026 },
  ].forEach(({ frequency, delay, peak }) => {
    const osc = ctx.createOscillator();
    const harmonic = ctx.createOscillator();
    const gain = ctx.createGain();
    const harmonicGain = ctx.createGain();
    const start = now + delay;
    const end = start + 1.65;
    osc.type = "triangle";
    osc.frequency.value = frequency;
    harmonic.type = "sine";
    harmonic.frequency.value = frequency * 2;
    gain.gain.setValueAtTime(0.0001, start);
    gain.gain.linearRampToValueAtTime(peak, start + 0.16);
    gain.gain.exponentialRampToValueAtTime(0.0001, end);
    harmonicGain.gain.setValueAtTime(0.0001, start);
    harmonicGain.gain.linearRampToValueAtTime(peak * 0.18, start + 0.2);
    harmonicGain.gain.exponentialRampToValueAtTime(0.0001, end);
    osc.connect(gain).connect(ctx.destination);
    harmonic.connect(harmonicGain).connect(ctx.destination);
    osc.start(start);
    harmonic.start(start);
    osc.stop(end);
    harmonic.stop(end);
  });
}

function updateChimeLoop() {
  const ringing = timers.some((timer) => timer.ringing);
  document.title = ringing ? "Timer ringing - AI Command Center" : previousTitle;
  if (ringing && !chimeTimer) {
    playChime();
    chimeTimer = setInterval(playChime, 4000);
  } else if (!ringing && chimeTimer) {
    clearInterval(chimeTimer);
    chimeTimer = null;
  }
}

function renderTimers() {
  const now = Date.now();
  let changed = false;
  for (const timer of timers) {
    if (!timer.ringing && timer.targetAt <= now) {
      timer.ringing = true;
      changed = true;
    }
  }
  timers.sort((a, b) => Number(b.ringing) - Number(a.ringing) || a.targetAt - b.targetAt);
  if (changed) saveTimers();

  timerNow.textContent = new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit", second: "2-digit" });
  const next = timers.find((timer) => !timer.ringing);
  const ringing = timers.find((timer) => timer.ringing);
  timerCount.classList.toggle("active", Boolean(next || ringing));
  timerCount.classList.toggle("ringing", Boolean(ringing));
  if (ringing) {
    timerCount.textContent = "ringing";
    timerCount.title = `${timerTitle(ringing)} is ringing${timers.length > 1 ? ` · ${timers.length} timers` : ""}`;
  } else if (next) {
    timerCount.textContent = formatHeaderDuration(next.targetAt - now);
    timerCount.title = `${timerTitle(next)} in ${formatDuration(next.targetAt - now)}${timers.length > 1 ? ` · ${timers.length} timers` : ""}`;
  } else {
    timerCount.textContent = String(timers.length);
    timerCount.title = timers.length ? `${timers.length} timers` : "No timers set";
  }
  timerNext.textContent = timers.some((timer) => timer.ringing)
    ? "Timer ringing"
    : next
      ? `${timerTitle(next)} in ${formatDuration(next.targetAt - now)}`
      : "No timers set";

  if (!timers.length) {
    const li = document.createElement("li");
    li.className = "timer-empty";
    li.textContent = "No timers set.";
    timerList.replaceChildren(li);
    updateChimeLoop();
    return;
  }

  timerList.replaceChildren(...timers.map((timer) => {
    const li = document.createElement("li");
    li.classList.toggle("ringing", timer.ringing);
    const main = document.createElement("div");
    main.className = "timer-item-main";
    const label = document.createElement("b");
    label.textContent = timerTitle(timer);
    const remaining = document.createElement("span");
    remaining.textContent = timer.ringing
      ? "ringing"
      : timer.type === "alarm"
        ? `${formatDuration(timer.targetAt - now)} left`
        : formatDuration(timer.targetAt - now);
    main.append(label, remaining);
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = timer.ringing ? "Stop" : "Clear";
    button.addEventListener("click", () => {
      timers = timers.filter((item) => item.id !== timer.id);
      saveTimers();
      renderTimers();
    });
    li.append(main, button);
    return li;
  }));
  updateChimeLoop();
}

timerModeCountdown.addEventListener("click", () => setTimerMode("countdown"));
timerModeAlarm.addEventListener("click", () => setTimerMode("alarm"));
timerForm.addEventListener("submit", (event) => {
  event.preventDefault();
  try {
    ensureAudio();
    const targetAt = timerMode === "alarm" ? parseAlarmTime(timerValue.value) : parseCountdown(timerValue.value);
    timers.push({
      id: crypto.randomUUID(),
      type: timerMode,
      label: timerLabel.value.trim(),
      targetAt,
      ringing: false,
    });
    timerLabel.value = "";
    timerValue.value = "";
    saveTimers();
    renderTimers();
  } catch (err) {
    timerNext.textContent = err.message;
  }
});
setTimerMode(timerMode);

function fmtTime(ts) {
  const d = new Date(ts);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function fmtDay(ts) {
  return new Date(ts).toLocaleDateString([], { weekday: "short", month: "short", day: "numeric" });
}

function renderText(container, text) {
  // textContent-only rendering; @mentions get a span, never HTML injection.
  let cursor = 0;
  for (const match of text.matchAll(MENTION_RE)) {
    if (match.index > cursor) container.append(text.slice(cursor, match.index));
    const span = document.createElement("span");
    span.className = "mention";
    span.textContent = match[0];
    container.append(span);
    cursor = match.index + match[0].length;
  }
  if (cursor < text.length) container.append(text.slice(cursor));
}

const SUMMARY_LABEL_RE = /^(Need|Done|Next|Blocker|Review|Tests?|Refs?|Issue|Options?|Recommendation|Status|Warning|Files?)\s*:\s*(.*)$/i;

function appendSummaryText(container, text) {
  const fragment = document.createDocumentFragment();
  renderText(fragment, text);
  container.append(fragment);
}

function normalizeSummaryLines(summary) {
  return String(summary || "")
    .replace(/\r\n/g, "\n")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .slice(0, 8);
}

function summaryLabelName(label) {
  const lower = label.toLowerCase();
  if (lower === "test") return "Tests";
  if (lower === "ref") return "Refs";
  if (lower === "option") return "Options";
  return label.charAt(0).toUpperCase() + label.slice(1).toLowerCase();
}

function appendSummaryBulletList(container, lines) {
  const ul = document.createElement("ul");
  ul.className = "gist-bullets";
  for (const line of lines) {
    const li = document.createElement("li");
    appendSummaryText(li, line.replace(/^[-*]\s+/, ""));
    ul.append(li);
  }
  container.append(ul);
}

function appendSummaryRow(container, label, text) {
  const row = document.createElement("div");
  row.className = "gist-row";
  const tag = document.createElement("span");
  tag.className = "gist-label";
  tag.textContent = summaryLabelName(label);
  const body = document.createElement("span");
  body.className = "gist-text";
  appendSummaryText(body, text);
  row.append(tag, body);
  container.append(row);
}

function renderRelaySummary(container, summary) {
  const lines = normalizeSummaryLines(summary);
  if (lines.length <= 1) {
    container.classList.add("plain");
    appendSummaryText(container, lines[0] || "");
    return;
  }

  let index = 0;
  const firstLabel = lines[0].match(SUMMARY_LABEL_RE);
  if (!firstLabel && !/^[-*]\s+/.test(lines[0])) {
    const lead = document.createElement("div");
    lead.className = "gist-lead";
    appendSummaryText(lead, lines[0]);
    container.append(lead);
    index = 1;
  }

  let bulletBuffer = [];
  const flushBullets = () => {
    if (!bulletBuffer.length) return;
    appendSummaryBulletList(container, bulletBuffer);
    bulletBuffer = [];
  };

  for (; index < lines.length; index += 1) {
    const line = lines[index];
    if (/^[-*]\s+/.test(line)) {
      bulletBuffer.push(line);
      continue;
    }
    flushBullets();
    const labeled = line.match(SUMMARY_LABEL_RE);
    if (labeled) {
      appendSummaryRow(container, labeled[1], labeled[2]);
    } else {
      const detail = document.createElement("div");
      detail.className = "gist-detail";
      appendSummaryText(detail, line);
      container.append(detail);
    }
  }
  flushBullets();
}

function addMessage(msg) {
  const day = fmtDay(msg.ts);
  if (day !== lastDay) {
    const divider = document.createElement("div");
    divider.className = "day-divider";
    divider.textContent = day;
    feed.append(divider);
    lastDay = day;
  }
  if (msg.sender === "[hcom-events]") {
    const note = document.createElement("div");
    note.className = "sysnote";
    note.textContent = msg.text.slice(0, 200);
    feed.append(note);
    return;
  }
  const node = document.createElement("div");
  node.className = "msg" + (msg.sender === operator ? " self" : "");
  const meta = document.createElement("div");
  meta.className = "meta";
  const sender = document.createElement("span");
  sender.className = "sender";
  sender.textContent = msg.sender === operator ? "you" : msg.sender;
  const time = document.createElement("span");
  time.textContent = fmtTime(msg.ts);
  meta.append(sender, time);
  if (msg.intent === "request") {
    const intent = document.createElement("span");
    intent.className = "intent-request";
    intent.textContent = "needs reply";
    meta.append(intent);
  }
  if (msg.sender !== operator) {
    const replyBtn = document.createElement("button");
    replyBtn.type = "button";
    replyBtn.className = "reply-btn";
    replyBtn.textContent = "reply";
    replyBtn.addEventListener("click", () =>
      startReply({ id: msg.id, sender: msg.sender, text: msg.summary || msg.text }));
    meta.append(replyBtn);
  }
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  if (msg.quote) {
    const quote = document.createElement("div");
    quote.className = "quote";
    const who = document.createElement("b");
    who.textContent = msg.quote.sender;
    const what = document.createElement("span");
    what.textContent = msg.quote.text;
    quote.append(who, what);
    quote.addEventListener("click", () => {
      const target = nodes.get(msg.quote.id);
      if (target) {
        target.scrollIntoView({ behavior: "smooth", block: "center" });
        target.classList.add("flash");
        setTimeout(() => target.classList.remove("flash"), 1200);
      }
    });
    node.append(meta, quote, bubble);
  } else {
    node.append(meta, bubble);
  }
  renderBubble(bubble, msg);
  bubbles.set(msg.id, { bubble, msg });
  nodes.set(msg.id, node);
  feed.append(node);
}

function renderBubble(bubble, msg) {
  bubble.replaceChildren();
  if (gistsEnabled && msg.summary && msg.sender_kind === "instance" && msg.sender !== operator) {
    const gist = document.createElement("div");
    gist.className = "gist";
    renderRelaySummary(gist, msg.summary);
    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "raw-toggle";
    toggle.textContent = "relay · show original";
    const raw = document.createElement("div");
    raw.className = "raw-text";
    raw.hidden = true;
    renderText(raw, msg.text);
    toggle.addEventListener("click", () => {
      raw.hidden = !raw.hidden;
      toggle.textContent = raw.hidden ? "relay · show original" : "relay · hide original";
    });
    bubble.append(gist, toggle, raw);
  } else {
    renderText(bubble, msg.text);
  }
}

async function pollSummaries() {
  if (!gistsEnabled || bubbles.size === 0) return;
  const pending = [...bubbles.values()].filter((e) => !e.msg.summary);
  if (!pending.length) return;
  const oldest = Math.min(...pending.map((e) => e.msg.id));
  try {
    const res = await fetch(`/api/summaries?since=${oldest - 1}`);
    const data = await res.json();
    if (!data.ok) return;
    for (const [id, summary] of Object.entries(data.summaries)) {
      const entry = bubbles.get(Number(id));
      if (entry && !entry.msg.summary) {
        entry.msg.summary = summary;
        renderBubble(entry.bubble, entry.msg);
      }
    }
  } catch { /* best-effort */ }
}

async function poll() {
  try {
    const res = await fetch(`/api/chat?since=${lastId}&limit=200`);
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "chat read failed");
    operator = data.operator || operator;
    const atBottom = feed.scrollHeight - feed.scrollTop - feed.clientHeight < 80;
    for (const msg of data.messages) {
      addMessage(msg);
      lastId = Math.max(lastId, msg.id);
    }
    if (data.messages.length && atBottom) feed.scrollTop = feed.scrollHeight;
    connStatus.textContent = `connected as ${operator}`;
  } catch (err) {
    connStatus.textContent = `offline: ${err.message}`;
  }
}

async function pollPresence(options = {}) {
  try {
    const res = await fetch(`/api/presence${options.refresh ? "?refresh=1" : ""}`);
    const data = await res.json();
    if (!data.ok) return;
    knownAgents = data.agents.map((a) => a.name);
    providerUsage = data.provider_usage || {};
    const rows = [...data.agents, ...(data.shortcuts || [])];
    presenceCount.textContent = String(rows.length);
    presenceList.replaceChildren(...renderPresenceGroups(rows));
  } catch { /* sidebar is best-effort */ }
}

const TOOL_ORDER = ["claude", "codex", "ollama", "gemini", "opencode", "unknown"];

function toolSortKey(tool) {
  const idx = TOOL_ORDER.indexOf(tool || "unknown");
  return idx === -1 ? TOOL_ORDER.length : idx;
}

function renderPresenceGroups(agents) {
  const groups = new Map();
  for (const agent of agents) {
    const tool = agent.tool || "unknown";
    if (!groups.has(tool)) groups.set(tool, []);
    groups.get(tool).push(agent);
  }
  return [...groups.entries()]
    .sort(([a], [b]) => toolSortKey(a) - toolSortKey(b) || a.localeCompare(b))
    .flatMap(([tool, members]) => {
      const collapsed = localStorage.getItem(`presence-group:${tool}:collapsed`) === "1";
      return [
        presenceGroupHeader(tool, members, collapsed, providerUsage[tool]),
        ...members.map((agent) => renderPresenceAgent(agent, { group: tool, collapsed })),
      ];
    });
}

function presenceGroupHeader(tool, members, collapsed, sharedUsage = null) {
  const li = document.createElement("li");
  li.className = "presence-group";
  li.classList.toggle("collapsed", collapsed);
  li.dataset.group = tool;
  const top = document.createElement("div");
  top.className = "presence-group-top";
  const usage = sharedUsage || groupUsageSummary(members);
  const label = document.createElement("span");
  label.textContent = members[0]?.tool_label || tool || "Other";
  const count = document.createElement("span");
  count.textContent = String(members.length);
  if (usage.kind === "limit" && usage.remaining_label) {
    const reset = document.createElement("span");
    reset.className = "presence-group-reset";
    reset.textContent = usage.remaining_label;
    top.append(label, reset, count);
  } else {
    top.append(label, count);
  }
  li.append(top, renderUsageBar(usage, { compact: true }));
  li.title = [
    `${collapsed ? "Expand" : "Collapse"} ${label.textContent}`,
    usage.label,
    usage.remaining_label,
  ].filter(Boolean).join(" · ");
  li.addEventListener("click", () => {
    localStorage.setItem(`presence-group:${tool}:collapsed`, collapsed ? "0" : "1");
    pollPresence();
  });
  return li;
}

function formatTokenCount(value) {
  if (typeof value !== "number") return "";
  return value.toLocaleString();
}

function usageTitle(agent) {
  const usage = agent.usage || {};
  const chunks = [
    agent.status,
    agent.context,
    agent.model ? `model: ${agent.model}` : "",
    usage.total_tokens ? `tokens: ${formatTokenCount(usage.total_tokens)}` : "",
    usage.non_cached_tokens ? `non-cached: ${formatTokenCount(usage.non_cached_tokens)}` : "",
    usage.limit_text || "",
  ].filter(Boolean);
  return chunks.join(" · ");
}

function usageRank(status) {
  return { error: 3, warn: 2, ok: 1, unknown: 0 }[status] ?? 0;
}

function formatUsagePercent(value) {
  return `${value.toFixed(1).replace(/\.0$/, "")}%`;
}

function groupUsageSummary(members) {
  const usages = members.map((agent) => agent.usage || {});
  const limits = usages.filter((usage) => usage.kind === "limit" || usage.status === "error");
  if (limits.length) {
    return {
      kind: "limit",
      status: "error",
      label: `${limits.length} limit note${limits.length === 1 ? "" : "s"}`,
      remaining_label: "reset noted",
      used_percent: 100,
    };
  }

  const percentUsages = usages.filter((usage) => typeof usage.used_percent === "number");
  if (percentUsages.length) {
    const highest = percentUsages.reduce((best, usage) => (
      usage.used_percent > best.used_percent ? usage : best
    ));
    const used = Math.max(0, Math.min(100, highest.used_percent));
    return {
      ...highest,
      label: `${formatUsagePercent(used)} used`,
      remaining_label: `${formatUsagePercent(Math.max(0, 100 - used))} left`,
      used_percent: used,
      status: highest.status || "unknown",
    };
  }

  const totalTokens = usages.reduce((sum, usage) => sum + Number(usage.total_tokens || 0), 0);
  const nonCachedTokens = usages.reduce((sum, usage) => sum + Number(usage.non_cached_tokens || 0), 0);
  const observed = usages.find((usage) => usage.kind === "observed");
  if (totalTokens || nonCachedTokens || observed) {
    return {
      kind: "observed",
      status: "unknown",
      label: nonCachedTokens ? `${formatTokenCount(nonCachedTokens)} non-cached` : "observed usage",
      remaining_label: "no % exposed",
      used_percent: null,
      total_tokens: totalTokens || undefined,
      non_cached_tokens: nonCachedTokens || undefined,
    };
  }

  const local = usages.find((usage) => usage.kind === "local");
  if (local) {
    return {
      kind: "local",
      status: "unknown",
      label: "local/on demand",
      remaining_label: "no shared limit",
      used_percent: null,
    };
  }

  const status = usages.reduce((best, usage) => (
    usageRank(usage.status) > usageRank(best) ? usage.status : best
  ), "unknown");
  return {
    kind: "unknown",
    status,
    label: "usage unknown",
    remaining_label: "unknown",
    used_percent: null,
  };
}

function renderUsageBar(usage = {}, options = {}) {
  const wrap = document.createElement("div");
  wrap.className = "usage-wrap" + (options.compact ? " compact" : "");

  const track = document.createElement("div");
  track.className = "usage-bar";
  track.dataset.status = usage.status || "unknown";
  track.dataset.kind = usage.kind || "unknown";

  const fill = document.createElement("span");
  fill.className = "usage-fill";
  const used = typeof usage.used_percent === "number" ? Math.max(0, Math.min(100, usage.used_percent)) : null;
  fill.style.width = used === null ? "100%" : `${Math.max(used, 3)}%`;
  track.append(fill);

  const labels = document.createElement("div");
  labels.className = "usage-line";
  const left = document.createElement("span");
  left.textContent = usage.label || "usage unknown";
  const right = document.createElement("span");
  right.textContent = usage.remaining_label || "unknown";
  labels.append(left, right);

  wrap.append(track, labels);
  return wrap;
}

function renderPresenceAgent(agent, options = {}) {
  const li = document.createElement("li");
  li.className = "presence-agent" + (agent.shortcut ? " shortcut" : "");
  if (options.group) li.dataset.group = options.group;
  li.classList.toggle("group-collapsed", Boolean(options.collapsed));
  li.title = usageTitle(agent);

  const top = document.createElement("div");
  top.className = "presence-top";
  const dot = document.createElement("span");
  dot.className = `dot ${["active", "listening", "blocked", "available"].includes(agent.status) ? agent.status : "unknown"}`;
  const name = document.createElement("span");
  name.className = "presence-name";
  name.textContent = agent.name;
  const model = document.createElement("span");
  model.className = "model-chip";
  model.textContent = agent.model || agent.tool_label || "model unknown";
  const actionBtn = document.createElement("button");
  actionBtn.className = "screen-btn";
  actionBtn.type = "button";
  if (agent.shortcut) {
    actionBtn.textContent = "launch";
    actionBtn.disabled = agent.launchable === false;
    actionBtn.title = `Launch ${agent.name}`;
    actionBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      launchLocalAgent(agent.id);
    });
  } else {
    actionBtn.textContent = "view";
    actionBtn.title = `Watch ${agent.name}'s terminal`;
    actionBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      openScreen(agent.name);
    });
  }
  top.append(dot, name, model, actionBtn);

  const meta = document.createElement("div");
  meta.className = "presence-meta";
  const tag = document.createElement("span");
  tag.className = "tag";
  tag.textContent = agent.tag || agent.tool_label || "";
  meta.append(tag);

  li.append(top, meta);
  if (agent.shortcut) {
    li.addEventListener("click", () => launchLocalAgent(agent.id));
  } else {
    li.addEventListener("click", () => {
      input.value = `@${agent.name} ${input.value.replace(/^@[\w-]+\s*/, "")}`;
      input.focus();
    });
  }
  return li;
}

async function launchLocalAgent(id) {
  try {
    const res = await fetch("/api/local-agent/launch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id }),
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "launch failed");
    connStatus.textContent = data.already_running
      ? `${data.name} already running`
      : `launching ${data.name || id}`;
    setTimeout(() => {
      pollPresence();
      if (data.name) openScreen(data.name);
    }, data.already_running ? 250 : 1800);
  } catch (err) {
    connStatus.textContent = `local launch failed: ${err.message}`;
  }
}

async function pollMap() {
  try {
    const res = await fetch("/api/tasks");
    const data = await res.json();
    if (!data.ok) return;
    const counts = data.counts || {};
    const active = (data.active || []).length;
    const ready = counts.READY || 0;
    const inProgress = counts.IN_PROGRESS || 0;
    const submitted = counts.SUBMITTED || 0;
    const changes = counts.CHANGES_REQUESTED || 0;
    const blocked = counts.BLOCKED || 0;
    const parts = [
      `${data.total} total`,
      active ? `${active} active` : "no active queue",
      ready ? `${ready} ready` : "",
      inProgress ? `${inProgress} in progress` : "",
      submitted ? `${submitted} submitted` : "",
      changes ? `${changes} changes requested` : "",
      blocked ? `${blocked} blocked` : "",
    ].filter(Boolean);
    mapSummary.textContent = parts.join(" · ");
    labSectionState.textContent = active ? String(active) : "idle";
  } catch { /* best-effort */ }
}

const MAP_HEALTH_LABELS = {
  runner: "Runner",
  librarian: "Librarian",
  replay: "Replay",
  rns: "RnS",
  tokens: "Tokens",
  cost_yield: "Yield",
  outcomes: "Outcomes",
};

function renderHealthText(text) {
  const wrap = document.createElement("span");
  wrap.className = "health-text";
  const parts = String(text || "").split("·").map((part) => part.trim()).filter(Boolean);
  if (parts.length <= 1) {
    wrap.textContent = text || "";
    return wrap;
  }
  wrap.replaceChildren(...parts.map((part) => {
    const chip = document.createElement("span");
    chip.className = "health-part";
    chip.textContent = part;
    return chip;
  }));
  return wrap;
}

function renderMapHealth(data) {
  mapHealthOverall.dataset.status = data.overall || "error";
  if (data.overall && labSectionState.textContent === "idle") labSectionState.textContent = data.overall;
  mapHealthRows.replaceChildren(...Object.entries(MAP_HEALTH_LABELS).map(([key, label]) => {
    const source = (data.sources || {})[key] || { status: "error", text: "missing" };
    const li = document.createElement("li");
    const dot = document.createElement("span");
    dot.className = "health-dot";
    dot.dataset.status = source.status || "error";
    const name = document.createElement("b");
    name.textContent = label;
    li.append(dot, name, renderHealthText(source.text));
    li.title = source.text || "";
    return li;
  }));
}

async function pollMapHealth(options = {}) {
  try {
    const res = await fetch(`/api/map/health${options.refresh ? "?refresh=1" : ""}`);
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "health unavailable");
    renderMapHealth(data);
  } catch (err) {
    mapHealthOverall.dataset.status = "error";
    const li = document.createElement("li");
    li.textContent = `health check offline: ${err.message}`;
    mapHealthRows.replaceChildren(li);
  }
}

async function refreshUsageNow() {
  usageRefreshBtn.disabled = true;
  usageRefreshState.textContent = "checking transcripts...";
  try {
    const res = await fetch("/api/usage/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "refresh failed");
    const presence = data.presence || {};
    const health = data.health || {};
    if (presence.ok) {
      knownAgents = presence.agents.map((a) => a.name);
      providerUsage = presence.provider_usage || {};
      const rows = [...presence.agents, ...(presence.shortcuts || [])];
      presenceCount.textContent = String(rows.length);
      presenceList.replaceChildren(...renderPresenceGroups(rows));
    } else {
      await pollPresence({ refresh: true });
    }
    if (health.ok) {
      renderMapHealth(health);
    } else {
      await pollMapHealth({ refresh: true });
    }
    usageRefreshState.textContent = `updated ${new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}`;
  } catch (err) {
    usageRefreshState.textContent = `refresh failed: ${err.message}`;
  } finally {
    usageRefreshBtn.disabled = false;
  }
}

usageRefreshBtn.addEventListener("click", refreshUsageNow);

function fmtExportAge(exportedAt) {
  if (!exportedAt) return "";
  const when = new Date(exportedAt);
  if (Number.isNaN(when.getTime())) return "";
  const minutes = Math.max(0, Math.round((Date.now() - when.getTime()) / 60000));
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}

function projectDaysIdle(project) {
  if (typeof project.daysIdle === "number") return project.daysIdle;
  if (!project.lastVisited) return null;
  const when = new Date(project.lastVisited);
  if (Number.isNaN(when.getTime())) return null;
  return Math.max(0, Math.floor((Date.now() - when.getTime()) / DAY_MS));
}

function projectDaysUntilDue(project) {
  if (typeof project.daysUntilDue === "number") return project.daysUntilDue;
  if (!project.dueDate) return null;
  const when = new Date(project.dueDate);
  if (Number.isNaN(when.getTime())) return null;
  return Math.round((when.getTime() - Date.now()) / DAY_MS);
}

function projectIsActive(project) {
  return !["Finished", "Archived"].includes(project.status || "");
}

function projectIsStale(project) {
  if (typeof project.isStale === "boolean") return project.isStale;
  const idle = projectDaysIdle(project);
  const reminder = Number(project.reminderDays || 14);
  return projectIsActive(project) && idle !== null && idle >= reminder;
}

function projectIsDue(project) {
  if (typeof project.isDue === "boolean") return project.isDue;
  const due = projectDaysUntilDue(project);
  return projectIsActive(project) && due !== null && due >= 0 && due <= 7;
}

function localProjectUpdaterSnapshot() {
  try {
    const raw = localStorage.getItem(PROJECT_UPDATER_STORE_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw);
    if (!Array.isArray(data.projects)) return null;
    const projects = data.projects.map((project) => ({
      name: project.name || "Untitled project",
      area: project.area || "General",
      status: project.status || "Active",
      priority: project.priority || "Medium",
      progress: Math.max(0, Math.min(100, Number(project.progress || 0))),
      reminderDays: Number(project.reminderDays || 14),
      daysIdle: projectDaysIdle(project),
      daysUntilDue: projectDaysUntilDue(project),
      isStale: projectIsStale(project),
      isDue: projectIsDue(project),
      nextAction: project.nextAction || "",
      referencePath: project.referencePath || "",
    }));
    const active = projects.filter(projectIsActive);
    return {
      source: "embedded",
      stats: {
        active: active.length,
        stale: active.filter(projectIsStale).length,
        dueSoon: active.filter(projectIsDue).length,
      },
      projects,
    };
  } catch {
    return null;
  }
}

function exportedProjectUpdaterSnapshot(exported) {
  if (!exported || !Array.isArray(exported.projects)) return null;
  return {
    source: "export",
    exportedAt: exported.exportedAt,
    stats: exported.stats || {},
    projects: exported.projects.map((project) => ({
      name: project.name || "Untitled project",
      area: project.area || "General",
      status: project.status || "Active",
      priority: project.priority || "Medium",
      progress: Math.max(0, Math.min(100, Number(project.progress || 0))),
      reminderDays: Number(project.reminderDays || 14),
      daysIdle: typeof project.daysIdle === "number" ? project.daysIdle : null,
      daysUntilDue: typeof project.daysUntilDue === "number" ? project.daysUntilDue : null,
      isStale: Boolean(project.isStale),
      isDue: Boolean(project.isDue),
      nextAction: project.nextAction || "",
      referencePath: project.referencePath || "",
    })),
  };
}

function projectStatus(project) {
  if (project.status === "Finished") return { key: "finished", label: "finished" };
  if (project.status === "Archived") return { key: "archived", label: "archived" };
  if (project.isStale) return { key: "stale", label: `${project.daysIdle ?? "?"}d idle` };
  if (project.isDue) {
    const due = project.daysUntilDue;
    const label = due === 0 ? "due today" : due === 1 ? "due tomorrow" : `due ${due}d`;
    return { key: "due", label };
  }
  return { key: "active", label: (project.status || "active").toLowerCase() };
}

function projectSortScore(project) {
  if (project.isStale) return 0;
  if (project.isDue) return 1;
  if (projectIsActive(project)) return 2;
  if (project.status === "Finished") return 3;
  return 4;
}

function renderProjectUpdaterProjects(snapshot) {
  const projects = snapshot?.projects || [];
  projectUpdaterCount.textContent = projects.length ? String(projects.length) : "0";
  if (!projects.length) {
    const li = document.createElement("li");
    li.className = "project-empty";
    li.textContent = snapshot?.source === "export"
      ? "No projects in exported snapshot."
      : "No embedded projects yet.";
    projectUpdaterProjects.replaceChildren(li);
    return;
  }
  const rows = projects
    .slice()
    .sort((a, b) => projectSortScore(a) - projectSortScore(b) || (b.daysIdle ?? -1) - (a.daysIdle ?? -1))
    .slice(0, 8)
    .map((project) => {
      const status = projectStatus(project);
      const li = document.createElement("li");
      li.className = "project-row";
      li.dataset.status = status.key;
      const top = document.createElement("div");
      top.className = "project-row-top";
      const name = document.createElement("span");
      name.className = "project-name";
      name.textContent = project.name;
      const badge = document.createElement("span");
      badge.className = "project-status";
      badge.textContent = status.label;
      top.append(name, badge);
      const meta = document.createElement("div");
      meta.className = "project-meta";
      meta.textContent = [project.area, project.nextAction ? `Next: ${project.nextAction}` : ""].filter(Boolean).join(" · ");
      const bar = document.createElement("div");
      bar.className = "project-progress";
      const fill = document.createElement("span");
      fill.style.width = `${project.progress}%`;
      bar.append(fill);
      li.append(top, meta, bar);
      li.title = `${project.name} · ${project.status || "Active"} · ${project.progress}%`;
      li.addEventListener("click", () => {
        pendingProjectSearch = project.name;
        openProjectUpdaterModal();
      });
      return li;
    });
  projectUpdaterProjects.replaceChildren(...rows);
}

async function pollProjectUpdater() {
  try {
    const res = await fetch("/api/project-updater/status");
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "status unavailable");
    projectUpdaterOpen.disabled = !data.app_exists;
    projectUpdaterModalOpen.disabled = !data.app_exists;
    projectUpdaterOpen.hidden = false;
    projectUpdaterModalOpen.hidden = false;
    projectUpdaterCard.title = data.app_path || "";
    projectUpdaterEmbeddedUrl = data.embedded_url || "/project-updater/";
    if (!data.app_exists) {
      projectUpdaterState.textContent = "missing";
      projectUpdaterSummary.textContent = "ProjectUpdater app file was not found.";
      return;
    }
    const localSnapshot = localProjectUpdaterSnapshot();
    const exported = data.status_export;
    const snapshot = localSnapshot || exportedProjectUpdaterSnapshot(exported);
    if (snapshot && snapshot.stats) {
      const stats = snapshot.stats;
      const age = snapshot.exportedAt ? fmtExportAge(snapshot.exportedAt) : "";
      const ageText = age ? ` · exported ${age}` : "";
      projectUpdaterState.textContent = snapshot.source === "embedded" ? "embedded data" : "export loaded";
      projectUpdaterSummary.textContent =
        `${stats.active ?? 0} active · ${stats.stale ?? 0} stale · ${stats.dueSoon ?? 0} due soon${ageText}`;
      renderProjectUpdaterProjects(snapshot);
    } else if (data.status_export_error) {
      projectUpdaterState.textContent = "export invalid";
      projectUpdaterSummary.textContent = `Status export exists but could not be read: ${data.status_export_error}`;
      renderProjectUpdaterProjects(null);
    } else {
      projectUpdaterState.textContent = data.command_bridge?.available ? "command bridge ready" : "manual export needed";
      projectUpdaterSummary.textContent = data.command_bridge?.available
        ? "Use ai project new/update/note to send changes into ProjectUpdater, then export status when you want this card refreshed."
        : `Open ProjectUpdater and use Export status to create ${data.status_export_path}.`;
      renderProjectUpdaterProjects(null);
    }
  } catch (err) {
    projectUpdaterState.textContent = "offline";
    projectUpdaterSummary.textContent = err.message;
    projectUpdaterOpen.disabled = true;
    projectUpdaterModalOpen.disabled = true;
    renderProjectUpdaterProjects(null);
  }
}

function openProjectUpdaterModal() {
  projectUpdaterModal.hidden = false;
  projectUpdaterModalNote.textContent = "embedded in Command Center";
  if (!projectUpdaterFrame.src) projectUpdaterFrame.src = projectUpdaterEmbeddedUrl;
  if (pendingProjectSearch) {
    projectUpdaterFrame.addEventListener("load", applyPendingProjectSearch, { once: true });
    if (projectUpdaterFrame.contentWindow) setTimeout(applyPendingProjectSearch, 250);
  }
  projectUpdaterModalClose.focus();
}

function applyPendingProjectSearch() {
  if (!pendingProjectSearch) return;
  try {
    const input = projectUpdaterFrame.contentDocument?.getElementById("search");
    if (!input) return;
    input.value = pendingProjectSearch;
    input.dispatchEvent(new Event("input", { bubbles: true }));
    pendingProjectSearch = "";
  } catch { /* iframe may not be ready yet */ }
}

function closeProjectUpdaterModal() {
  projectUpdaterModal.hidden = true;
  projectUpdaterModalOpen.focus();
  pollProjectUpdater();
}

projectUpdaterModalOpen.addEventListener("click", openProjectUpdaterModal);
projectUpdaterModalClose.addEventListener("click", closeProjectUpdaterModal);

projectUpdaterOpen.addEventListener("click", async () => {
  projectUpdaterOpen.disabled = true;
  const previous = projectUpdaterSummary.textContent;
  projectUpdaterSummary.textContent = "Opening ProjectUpdater…";
  try {
    const res = await fetch("/api/project-updater/open", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "open failed");
    projectUpdaterSummary.textContent = "ProjectUpdater opened. Use Export status there to refresh this card.";
    setTimeout(pollProjectUpdater, 1600);
  } catch (err) {
    projectUpdaterSummary.textContent = `Open failed: ${err.message}`;
    setTimeout(() => { projectUpdaterSummary.textContent = previous; }, 4000);
  } finally {
    projectUpdaterOpen.disabled = false;
  }
});

/* ---------- needs-attention inbox ---------- */

const dismissedAttention = new Set(JSON.parse(localStorage.getItem("attn-dismissed") || "[]"));

function gateItem(gate) {
  const li = document.createElement("li");
  li.className = "gate";
  const who = document.createElement("b");
  who.textContent = `MAP gate · ${gate.gate_id}`;
  const what = document.createElement("span");
  what.textContent = gate.name + (gate.after_task ? ` (after ${gate.after_task})` : "");
  const actions = document.createElement("div");
  actions.className = "gate-actions";
  for (const [label, approve] of [["Approve", true], ["Reject", false]]) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = approve ? "approve" : "reject";
    btn.textContent = label;
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      if (!confirm(`${label} MAP gate "${gate.name}" (${gate.gate_id})?`)) return;
      const res = await fetch("/api/gate/decide", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ gate_id: gate.gate_id, approve }),
      });
      const out = await res.json();
      if (!out.ok) alert(`Gate decision failed: ${out.error}`);
      pollAttention();
    });
    actions.append(btn);
  }
  li.append(who, what, actions);
  return li;
}

function promptItem(prompt) {
  const li = document.createElement("li");
  li.className = "prompt";
  const who = document.createElement("b");
  who.textContent = `${prompt.name} · waiting in terminal`;
  const what = document.createElement("span");
  what.textContent = (prompt.context || "needs a response") + " — click to open its screen";
  li.append(who, what);
  li.addEventListener("click", () => openScreen(prompt.name));
  return li;
}

async function pollAttention() {
  try {
    const [attnRes, apprRes] = await Promise.all([
      fetch("/api/attention"), fetch("/api/approvals"),
    ]);
    const data = await attnRes.json();
    const approvals = await apprRes.json();
    if (!data.ok) return;
    const items = data.items.filter((i) => !dismissedAttention.has(i.id));
    const extras = [
      ...(approvals.ok ? approvals.gates.map(gateItem) : []),
      ...(approvals.ok ? approvals.prompts.map(promptItem) : []),
    ];
    const total = items.length + extras.length;
    attentionHead.hidden = total === 0;
    attentionCount.textContent = total;
    attentionList.replaceChildren(
      ...extras,
      ...items.map((item) => {
        const li = document.createElement("li");
        const who = document.createElement("b");
        who.textContent = item.sender;
        const dismiss = document.createElement("button");
        dismiss.type = "button";
        dismiss.className = "attn-dismiss";
        dismiss.textContent = "×";
        dismiss.title = "Dismiss without answering";
        dismiss.addEventListener("click", (e) => {
          e.stopPropagation();
          dismissedAttention.add(item.id);
          localStorage.setItem("attn-dismissed", JSON.stringify([...dismissedAttention]));
          pollAttention();
        });
        who.append(dismiss);
        const what = document.createElement("span");
        what.textContent = (item.summary || item.text).slice(0, 90);
        li.append(who, what);
        li.title = item.text;
        li.addEventListener("click", () => {
          const target = nodes.get(item.id);
          if (target) {
            target.scrollIntoView({ behavior: "smooth", block: "center" });
            target.classList.add("flash");
            setTimeout(() => target.classList.remove("flash"), 1200);
          }
          startReply({ id: item.id, sender: item.sender, text: item.summary || item.text });
        });
        return li;
      }),
    );
  } catch { /* best-effort */ }
}

/* ---------- lab lifecycle ---------- */

async function pollLab() {
  try {
    const res = await fetch("/api/lab/status");
    const data = await res.json();
    if (!data.ok) return;
    if (data.agents.length) {
      labBanner.hidden = true;
    } else {
      labBannerText.textContent = data.launcher_available
        ? "Lab is offline — no agents in the room."
        : "Lab launcher not found on this machine.";
      labStartBtn.hidden = !data.launcher_available;
      labBanner.hidden = false;
    }
  } catch { /* best-effort */ }
}

labStartBtn.addEventListener("click", async () => {
  labStartBtn.disabled = true;
  labBannerText.textContent = "Starting lab…";
  try {
    const res = await fetch("/api/lab/start", { method: "POST", body: "{}" });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "start failed");
    labBannerText.textContent = "Lab starting — agents will appear shortly.";
  } catch (err) {
    labBannerText.textContent = `Lab start failed: ${err.message}`;
  } finally {
    labStartBtn.disabled = false;
  }
});

/* ---------- agent screen panel ---------- */

async function refreshScreen() {
  if (!screenAgent) return;
  try {
    const res = await fetch(`/api/term?name=${encodeURIComponent(screenAgent)}`);
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "screen read failed");
    const nearBottom = screenBody.scrollHeight - screenBody.scrollTop - screenBody.clientHeight < 40;
    screenBody.textContent = (data.screen.lines || []).join("\n");
    if (nearBottom) screenBody.scrollTop = screenBody.scrollHeight;
  } catch (err) {
    screenBody.textContent = `— ${err.message} —`;
  }
}

function openScreen(name) {
  screenAgent = name;
  screenTitle.textContent = `${name} — terminal`;
  screenBody.textContent = "loading…";
  screenPanel.hidden = false;
  refreshScreen();
  clearInterval(screenTimer);
  screenTimer = setInterval(refreshScreen, 2000);
  screenInput.focus();
}

function closeScreen() {
  screenAgent = null;
  screenPanel.hidden = true;
  clearInterval(screenTimer);
  input.focus();
}

async function inject(text, enter) {
  if (!screenAgent) return;
  try {
    const res = await fetch("/api/term/inject", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: screenAgent, text, enter }),
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.stderr || data.error || "inject failed");
    screenInput.value = "";
    setTimeout(refreshScreen, 300);
  } catch (err) {
    screenBody.textContent += `\n— inject failed: ${err.message} —`;
  }
}

screenForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = screenInput.value;
  if (!text && !confirm(`Send a bare Enter to ${screenAgent}?`)) return;
  inject(text, true);
});
screenEnterBtn.addEventListener("click", () => inject("", true));
document.querySelectorAll(".quick-keys button").forEach((btn) => {
  btn.addEventListener("click", () => inject(btn.dataset.key, false));
});
screenCloseBtn.addEventListener("click", closeScreen);
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !projectUpdaterModal.hidden) {
    closeProjectUpdaterModal();
    return;
  }
  if (e.key === "Escape" && !screenPanel.hidden) closeScreen();
});

/* ---------- mention autocomplete ---------- */

function currentMentionPrefix() {
  const upToCaret = input.value.slice(0, input.selectionStart ?? input.value.length);
  const match = upToCaret.match(/(?<![\w@])@([A-Za-z0-9_-]*)$/);
  return match ? match[1] : null;
}

function updateHint() {
  const prefix = currentMentionPrefix();
  if (prefix === null) {
    mentionHint.hidden = true;
    return;
  }
  const options = knownAgents.filter((n) => n.startsWith(prefix)).slice(0, 6);
  if (!options.length) {
    mentionHint.hidden = true;
    return;
  }
  hintIndex = Math.min(hintIndex, options.length - 1);
  mentionHint.replaceChildren(
    ...options.map((name, i) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = `@${name}`;
      btn.className = i === hintIndex ? "sel" : "";
      btn.addEventListener("click", () => applyMention(name));
      return btn;
    }),
  );
  mentionHint.hidden = false;
}

function applyMention(name) {
  const caret = input.selectionStart ?? input.value.length;
  const before = input.value.slice(0, caret).replace(/@[A-Za-z0-9_-]*$/, `@${name} `);
  input.value = before + input.value.slice(caret);
  mentionHint.hidden = true;
  input.focus();
  input.setSelectionRange(before.length, before.length);
}

/* ---------- sending ---------- */

async function send() {
  let text = input.value.trim();
  if (!text) return;
  const body = { text };
  if (replyTarget) {
    body.reply_to = String(replyTarget.id);
    if (!text.includes(`@${replyTarget.sender}`)) {
      body.text = text = `@${replyTarget.sender} ${text}`;
    }
  }
  sendBtn.disabled = true;
  try {
    const res = await fetch("/api/chat/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.stderr || data.error || "send failed");
    input.value = "";
    input.style.height = "auto";
    cancelReply();
    await poll();
    pollAttention();
    feed.scrollTop = feed.scrollHeight;
  } catch (err) {
    connStatus.textContent = `send failed: ${err.message}`;
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}

composer.addEventListener("submit", (e) => {
  e.preventDefault();
  send();
});

input.addEventListener("keydown", (e) => {
  if (!mentionHint.hidden) {
    const options = mentionHint.querySelectorAll("button");
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      hintIndex = (hintIndex + (e.key === "ArrowDown" ? 1 : options.length - 1)) % options.length;
      options.forEach((b, i) => b.classList.toggle("sel", i === hintIndex));
      return;
    }
    if (e.key === "Tab" || (e.key === "Enter" && options.length)) {
      e.preventDefault();
      options[hintIndex].click();
      return;
    }
    if (e.key === "Escape") {
      mentionHint.hidden = true;
      return;
    }
  }
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    send();
  }
});

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 160)}px`;
  hintIndex = 0;
  updateHint();
});

const gistCheckbox = document.getElementById("gist-checkbox");
gistCheckbox.checked = gistsEnabled;
gistCheckbox.addEventListener("change", () => {
  gistsEnabled = gistCheckbox.checked;
  localStorage.setItem("gists", gistsEnabled ? "on" : "off");
  for (const entry of bubbles.values()) renderBubble(entry.bubble, entry.msg);
});

poll().then(() => { feed.scrollTop = feed.scrollHeight; });
pollPresence();
pollMap();
pollMapHealth();
pollProjectUpdater();
pollLab();
pollAttention();
renderTimers();
setInterval(poll, 2000);
setInterval(pollAttention, 8000);
setInterval(pollPresence, 8000);
setInterval(pollMap, 30000);
setInterval(pollMapHealth, 30000);
setInterval(pollProjectUpdater, 30000);
setInterval(pollLab, 10000);
setInterval(pollSummaries, 4000);
setInterval(renderTimers, 250);
input.focus();
