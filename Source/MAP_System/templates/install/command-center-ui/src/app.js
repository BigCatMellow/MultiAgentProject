const agentButtons = Array.from(document.querySelectorAll(".agent-row"));
const messages = Array.from(document.querySelectorAll(".message"));
const scopeTitle = document.getElementById("scope-title");
const toggleWork = document.getElementById("toggle-work");
const workButtons = Array.from(document.querySelectorAll(".work-toggle"));
const composer = document.getElementById("composer");
const composerInput = document.getElementById("composer-input");
const actionResult = document.getElementById("action-result");

const labels = {
  all: "Conversation",
  codex: "codex-lab-maki · activity",
  claude: "claude-lab-taro · activity",
  monitor: "Monitor · attention",
  command: "command-center"
};

let allWorkOpen = false;

function setAgent(agent) {
  agentButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.agent === agent);
  });
  messages.forEach((message) => {
    message.classList.toggle("hidden", agent !== "all" && message.dataset.agent !== agent);
  });
  scopeTitle.textContent = labels[agent] || labels.all;
}

function setWorkOpen(open) {
  allWorkOpen = open;
  document.querySelectorAll(".work").forEach((panel) => panel.classList.toggle("open", open));
  workButtons.forEach((button) => {
    button.textContent = open ? "▾ Hide work" : "▸ Show work";
  });
  toggleWork.textContent = open ? "⊟ Collapse work" : "⊞ Expand work";
}

agentButtons.forEach((button) => {
  button.addEventListener("click", () => setAgent(button.dataset.agent));
});

workButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const panel = document.getElementById(button.dataset.target);
    const next = !panel.classList.contains("open");
    panel.classList.toggle("open", next);
    button.textContent = next ? "▾ Hide work" : "▸ Show work";
  });
});

toggleWork.addEventListener("click", () => setWorkOpen(!allWorkOpen));

document.querySelectorAll("[data-action]").forEach((button) => {
  button.addEventListener("click", () => {
    const action = button.dataset.action;
    const text = {
      approve: "Review request queued for claude-lab-taro.",
      inspect: "Opening TASK-055 details in the inspector.",
      hold: "Task remains in progress."
    };
    actionResult.textContent = text[action] || "";
  });
});

composer.addEventListener("submit", (event) => {
  event.preventDefault();
  const value = composerInput.value.trim();
  if (!value) return;

  const article = document.createElement("article");
  article.className = "message command";
  article.dataset.agent = "command";
  article.innerHTML = `
    <div class="avatar command">C</div>
    <div class="bubble">
      <div class="meta"><b>command-center</b><span>draft</span><time>now</time></div>
      <p></p>
    </div>`;
  article.querySelector("p").textContent = value;
  document.getElementById("feed").append(article);
  composerInput.value = "";
  article.scrollIntoView({ block: "nearest", behavior: "smooth" });
});

setAgent("all");
