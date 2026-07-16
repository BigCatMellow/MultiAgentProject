// Vanilla-JS port of the Studio design's Component class (state + isOpen/toggle/toggleAll semantics).
const state = {
  sel: "all",
  open: {},      // per-item explicit overrides: { verify: true, ... }
  allOpen: null,  // null = no global override yet, else true/false
};

const defaultDetail = "summaries"; // matches design prop default

function isOpen(id) {
  if (state.open[id] !== undefined) return state.open[id];
  if (state.allOpen !== null) return state.allOpen;
  return defaultDetail === "detailed";
}

function toggle(id) {
  state.open[id] = !isOpen(id);
  render();
}

function toggleAll() {
  const next = !(state.allOpen === null ? false : state.allOpen);
  state.allOpen = next;
  state.open = {};
  render();
}

function pick(agent) {
  state.sel = agent;
  render();
}

const scopeLabels = {
  all: "Conversation",
  nora: "nora · activity",
  miro: "miro · activity",
  monitor: "monitor · activity",
  "command-center": "command‑center",
};

const workIds = ["verify", "health", "review", "impl"];

function render() {
  // sidebar selection
  document.querySelectorAll(".cc-row[data-agent]").forEach((row) => {
    row.classList.toggle("active", row.dataset.agent === state.sel);
  });

  // feed filter
  document.querySelectorAll(".cc-msg[data-agent]").forEach((msg) => {
    const visible = state.sel === "all" || msg.dataset.agent === state.sel;
    msg.classList.toggle("hidden", !visible);
  });

  document.getElementById("scope-title").textContent = scopeLabels[state.sel] || scopeLabels.all;

  // per-item work panels
  workIds.forEach((id) => {
    const panel = document.getElementById(`raw-${id}`);
    const button = document.querySelector(`.cc-worktoggle[data-target="${id}"]`);
    const open = isOpen(id);
    if (panel) panel.classList.toggle("open", open);
    if (button) button.textContent = open ? "▾ Hide work" : "▸ Show work";
  });

  // expand/collapse all control
  const anyOpen = state.allOpen === true;
  document.getElementById("toggle-all").textContent = anyOpen ? "⊟ Collapse all" : "⊞ Expand all work";
}

document.querySelectorAll(".cc-row[data-agent]").forEach((row) => {
  row.addEventListener("click", () => pick(row.dataset.agent));
});

document.querySelectorAll(".cc-worktoggle[data-target]").forEach((button) => {
  button.addEventListener("click", () => toggle(button.dataset.target));
});

document.getElementById("toggle-all").addEventListener("click", toggleAll);

render();
