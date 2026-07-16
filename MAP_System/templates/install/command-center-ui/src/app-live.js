const statusEl = document.getElementById("server-status");
const workspaceEl = document.getElementById("workspace-path");
const taskTotalEl = document.getElementById("task-total");
const taskActiveEl = document.getElementById("task-active");
const eventCountEl = document.getElementById("event-count");
const hcomEl = document.getElementById("hcom-list");
const eventsList = document.getElementById("events-list");
const tasksList = document.getElementById("tasks-list");
const refreshBtn = document.getElementById("refresh-btn");
const sendForm = document.getElementById("send-form");
const sendResult = document.getElementById("send-result");
const identityHelp = document.getElementById("identity-help");
const sendButton = document.getElementById("send-button");
let hcomSendEnabled = false;

function item(title, body, meta = "") {
  const node = document.createElement("div");
  node.className = "app-item";
  const b = document.createElement("b");
  b.textContent = title;
  node.append(b);
  if (meta) {
    const span = document.createElement("span");
    span.textContent = meta;
    node.append(span);
  }
  if (body) {
    const p = document.createElement("p");
    p.textContent = body;
    node.append(p);
  }
  return node;
}

async function loadSnapshot() {
  statusEl.textContent = "Connecting...";
  const response = await fetch("/api/snapshot?limit=60");
  const data = await response.json();
  if (!data.ok) throw new Error("snapshot failed");

  workspaceEl.textContent = data.workspace;
  const tasks = data.tasks || {};
  const active = tasks.active || [];
  const events = data.events || [];
  taskTotalEl.textContent = tasks.total ?? "-";
  taskActiveEl.textContent = active.length;
  eventCountEl.textContent = events.length;
  hcomEl.textContent = data.hcom?.text || data.hcom?.error || "No hcom output";
  hcomSendEnabled = Boolean(data.hcom?.ok);
  const identity = data.hcom?.identity || "browser";
  identityHelp.classList.toggle("enabled", hcomSendEnabled);
  if (hcomSendEnabled) {
    identityHelp.textContent = `Sending is enabled. Messages will be attributed to hcom identity "${identity}".`;
    sendResult.textContent = "Ready to send through hcom.";
    sendButton.disabled = false;
  } else {
    identityHelp.replaceChildren(
      document.createTextNode("Read-only monitor mode. The app can show MAP state, but it will not send hcom messages until you start it with a registered hcom identity, for example: "),
      Object.assign(document.createElement("code"), { textContent: "COMMAND_CENTER_UI_AGENT_NAME=<registered_name> ./run-command-center-app.sh" }),
      document.createTextNode(". This prevents browser clicks from being falsely attributed to an agent.")
    );
    sendResult.textContent = "Send is disabled in read-only mode.";
    sendButton.disabled = true;
  }
  statusEl.textContent = "Connected to local backend";

  eventsList.replaceChildren(...events.slice().reverse().map((event) => {
    const title = `${event.type || "EVENT"} · ${event.task_id || "SESSION"}`;
    const meta = `${event.sender || "unknown"} · ${event.created_at || ""}`;
    return item(title, event.summary || "", meta);
  }));

  tasksList.replaceChildren(...active.slice().reverse().map((task) => {
    const title = `${task.task_id} · ${task.status}`;
    return item(title, task.title || "", task.owner ? `owner: ${task.owner}` : "");
  }));
}

refreshBtn.addEventListener("click", () => {
  loadSnapshot().catch((error) => {
    statusEl.textContent = `Error: ${error.message}`;
  });
});

sendForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const recipients = document.getElementById("recipients").value
    .split(/[,\s]+/)
    .map((value) => value.trim())
    .filter(Boolean);
  const intent = document.getElementById("intent").value;
  const body = document.getElementById("message").value.trim();
  if (!hcomSendEnabled) {
    sendResult.textContent = "Send is disabled until the app is started with a registered hcom identity.";
    return;
  }
  sendResult.textContent = "Sending...";
  try {
    const response = await fetch("/api/hcom/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ recipients, intent, body }),
    });
    const data = await response.json();
    sendResult.textContent = JSON.stringify(data, null, 2);
    if (data.ok) {
      document.getElementById("message").value = "";
      await loadSnapshot();
    }
  } catch (error) {
    sendResult.textContent = `Error: ${error.message}`;
  }
});

loadSnapshot().catch((error) => {
  statusEl.textContent = `Error: ${error.message}`;
});
