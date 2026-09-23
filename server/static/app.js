/* ===================================================================
   FlowETL — Vanilla JS Application
   No build step, no framework. ES2020+.
   =================================================================== */

// ─── Constants ───────────────────────────────────────────────────────────────

const API = {
  connectors: "/api/connectors",
  run:        "/api/pipeline/run",
  status:     (id) => `/api/pipeline/status/${id}`,
  history:    "/api/pipeline/history",
  stream:     (id) => `/stream/${id}`,
};

// Connector field definitions (what options each connector needs)
const CONNECTOR_FIELDS = {
  csv: [
    { key: "path",      label: "File Path",  type: "text",   placeholder: "data/patients.csv", required: true },
    { key: "delimiter", label: "Delimiter",  type: "text",   placeholder: ",",                 required: false },
    { key: "encoding",  label: "Encoding",   type: "text",   placeholder: "utf-8",             required: false },
  ],
  json: [
    { key: "path", label: "File Path", type: "text", placeholder: "data/patients.json", required: true },
  ],
  jsonl: [
    { key: "path", label: "File Path (JSONL)", type: "text", placeholder: "data/patients.jsonl", required: true },
  ],
  sqlite: [
    { key: "path",       label: "Database Path", type: "text", placeholder: "data/hospital.sqlite", required: true },
    { key: "table_name", label: "Table Name",     type: "text", placeholder: "patients",             required: false },
  ],
  mysql: [
    { key: "host",       label: "Host",     type: "text",     placeholder: "localhost",   required: true },
    { key: "port",       label: "Port",     type: "number",   placeholder: "3306",        required: false },
    { key: "database",   label: "Database", type: "text",     placeholder: "hospital_db", required: true },
    { key: "user",       label: "User",     type: "text",     placeholder: "root",        required: true },
    { key: "password",   label: "Password", type: "password", placeholder: "••••••••",    required: true },
    { key: "table_name", label: "Table",    type: "text",     placeholder: "patients",    required: false },
  ],
  postgresql: [
    { key: "host",       label: "Host",     type: "text",     placeholder: "localhost",    required: true },
    { key: "port",       label: "Port",     type: "number",   placeholder: "5432",         required: false },
    { key: "database",   label: "Database", type: "text",     placeholder: "hospital_dw",  required: true },
    { key: "user",       label: "User",     type: "text",     placeholder: "postgres",     required: true },
    { key: "password",   label: "Password", type: "password", placeholder: "••••••••",     required: true },
    { key: "table_name", label: "Table",    type: "text",     placeholder: "patients_dim", required: false },
  ],
};
CONNECTOR_FIELDS.postgres = CONNECTOR_FIELDS.postgresql;

const CONNECTOR_ICONS = {
  csv: "📄", json: "📋", jsonl: "📋",
  sqlite: "🗄️", mysql: "🐬", postgresql: "🐘", postgres: "🐘",
};

// ─── State ───────────────────────────────────────────────────────────────────

const state = {
  connectors: { sources: [], destinations: [] },
  selectedSource: null,
  selectedDestination: null,
  currentRunId: null,
  pipelineName: "My Pipeline",
  activeView: "dashboard",
  stats: { total: 0, success: 0, error: 0, lastDuration: null },
};

// ─── Utility ─────────────────────────────────────────────────────────────────

function $(sel, ctx = document) { return ctx.querySelector(sel); }
function $$(sel, ctx = document) { return [...ctx.querySelectorAll(sel)]; }

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k.startsWith("on")) node.addEventListener(k.slice(2).toLowerCase(), v);
    else node.setAttribute(k, v);
  }
  for (const ch of children) {
    if (typeof ch === "string") node.insertAdjacentHTML("beforeend", ch);
    else if (ch) node.appendChild(ch);
  }
  return node;
}

function formatDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("id-ID", { day: "2-digit", month: "short", year: "numeric" })
    + " " + d.toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function statusPill(status) {
  const map = { success: ["✓ Sukses", "pill-success"], error: ["✕ Error", "pill-error"],
                running: ["⟳ Berjalan", "pill-running"], pending: ["◎ Menunggu", "pill-pending"] };
  const [text, cls] = map[status] || ["—", "pill-pending"];
  return `<span class="pill ${cls}">${text}</span>`;
}

// ─── Toast ───────────────────────────────────────────────────────────────────

function toast(message, type = "info", duration = 4000) {
  const container = $("#toast-container");
  const t = el("div", { class: `toast toast-${type}` });
  const icons = { success: "✅", error: "❌", info: "ℹ️" };
  t.innerHTML = `<span>${icons[type] || "ℹ️"}</span><span>${message}</span>`;
  container.appendChild(t);
  setTimeout(() => {
    t.style.animation = "slideOut 0.3s cubic-bezier(0.4,0,0.2,1) forwards";
    setTimeout(() => t.remove(), 300);
  }, duration);
}

// ─── Navigation ──────────────────────────────────────────────────────────────

function showView(name) {
  state.activeView = name;
  $$(".view").forEach(v => v.classList.remove("active"));
  $(`#view-${name}`)?.classList.add("active");
  $$(".nav-item").forEach(n => n.classList.remove("active"));
  $(`[data-view="${name}"]`)?.classList.add("active");
  // Update topbar title
  const titles = { dashboard: "Dashboard", builder: "Pipeline Builder", history: "Pipeline History" };
  $("#topbar-title").textContent = titles[name] || name;
  if (name === "history") loadHistory();
  if (name === "dashboard") updateDashboardStats();
}

// ─── Connector Selection ──────────────────────────────────────────────────────

function renderConnectorChips(type, containerId, fieldContainerId) {
  const container = $(`#${containerId}`);
  if (!container) return;
  const list = type === "source" ? state.connectors.sources : state.connectors.destinations;
  container.innerHTML = "";
  for (const name of list) {
    const icon = CONNECTOR_ICONS[name] || "🔌";
    const chip = el("div", {
      class: `connector-chip${(type === "source" ? state.selectedSource : state.selectedDestination) === name ? " selected" : ""}`,
      onclick: () => {
        if (type === "source") state.selectedSource = name;
        else state.selectedDestination = name;
        renderConnectorChips(type, containerId, fieldContainerId);
        renderConnectorFields(name, fieldContainerId);
      },
    }, `${icon} ${name}`);
    container.appendChild(chip);
  }
}

function renderConnectorFields(connectorType, containerId) {
  const container = $(`#${containerId}`);
  if (!container) return;
  const fields = CONNECTOR_FIELDS[connectorType];
  if (!fields || fields.length === 0) {
    container.innerHTML = `<div class="empty-desc" style="font-size:12px;color:var(--text-3);padding:8px 0">Tidak ada opsi tambahan untuk connector ini.</div>`;
    return;
  }
  container.innerHTML = "";
  for (const f of fields) {
    const group = el("div", { class: "form-group" });
    group.innerHTML = `
      <label class="form-label">${f.label}${f.required ? '<span class="field-required">*</span>' : ''}</label>
      <input class="form-control" type="${f.type}" id="field-${containerId}-${f.key}"
             placeholder="${f.placeholder}" ${f.required ? "required" : ""} autocomplete="off">
    `;
    container.appendChild(group);
  }
}

function collectOptions(containerId, connectorType) {
  const fields = CONNECTOR_FIELDS[connectorType] || [];
  const opts = {};
  for (const f of fields) {
    const input = $(`#field-${containerId}-${f.key}`);
    if (input && input.value.trim()) {
      opts[f.key] = f.type === "number" ? Number(input.value) : input.value.trim();
    }
  }
  return opts;
}

// ─── Pipeline Builder ─────────────────────────────────────────────────────────

function initBuilder() {
  // Render source chips
  renderConnectorChips("source", "source-chips", "source-fields");
  renderConnectorChips("destination", "dest-chips", "dest-fields");

  // Pipeline name
  const nameInput = $("#pipeline-name-input");
  if (nameInput) {
    nameInput.value = state.pipelineName;
    nameInput.addEventListener("input", () => { state.pipelineName = nameInput.value || "My Pipeline"; });
  }

  // Run button
  const runBtn = $("#run-pipeline-btn");
  if (runBtn) runBtn.addEventListener("click", handleRunPipeline);
}

async function handleRunPipeline() {
  if (!state.selectedSource) { toast("Pilih Source connector terlebih dahulu.", "error"); return; }
  if (!state.selectedDestination) { toast("Pilih Destination connector terlebih dahulu.", "error"); return; }

  const srcOpts = collectOptions("source-fields", state.selectedSource);
  const dstOpts = collectOptions("dest-fields", state.selectedDestination);

  // Basic validation
  const srcFields = CONNECTOR_FIELDS[state.selectedSource] || [];
  for (const f of srcFields) {
    if (f.required && !srcOpts[f.key]) {
      toast(`Source: field "${f.label}" wajib diisi.`, "error"); return;
    }
  }
  const dstFields = CONNECTOR_FIELDS[state.selectedDestination] || [];
  for (const f of dstFields) {
    if (f.required && !dstOpts[f.key]) {
      toast(`Destination: field "${f.label}" wajib diisi.`, "error"); return;
    }
  }

  const runBtn = $("#run-pipeline-btn");
  runBtn.disabled = true;
  runBtn.innerHTML = `<div class="spinner"></div> Memulai...`;

  try {
    const res = await fetch(API.run, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        pipeline_name: state.pipelineName,
        source_type: state.selectedSource,
        source_options: srcOpts,
        destination_type: state.selectedDestination,
        destination_options: dstOpts,
      }),
    });

    const data = await res.json();
    if (!res.ok) {
      toast(data.detail || "Terjadi kesalahan.", "error");
      return;
    }

    state.currentRunId = data.run_id;
    toast(`Pipeline dikirim! run_id: ${data.run_id}`, "info");
    openProgressDrawer(data.run_id);
    startSSEStream(data.run_id);

  } catch (err) {
    toast(`Error: ${err.message}`, "error");
  } finally {
    runBtn.disabled = false;
    runBtn.innerHTML = `▶ Jalankan Pipeline`;
  }
}

// ─── Progress Drawer & SSE ────────────────────────────────────────────────────

function openProgressDrawer(runId) {
  const drawer = $("#progress-drawer");
  drawer.classList.add("open");
  $("#drawer-run-id").textContent = `Run ID: ${runId}`;
  $("#progress-bar-fill").style.width = "0%";
  $("#log-console").innerHTML = "";
  updateDrawerStatus("running");
}

function closeProgressDrawer() {
  $("#progress-drawer").classList.remove("open");
}

function updateDrawerStatus(status) {
  const el = $("#drawer-status-pill");
  if (el) el.outerHTML = `<span id="drawer-status-pill">${statusPill(status)}</span>`;
}

function appendLog(line, type = "info") {
  const console_ = $("#log-console");
  const lineEl = document.createElement("div");
  lineEl.className = `log-line-${type}`;
  lineEl.textContent = line;
  console_.appendChild(lineEl);
  console_.scrollTop = console_.scrollHeight;
}

let activeEventSource = null;

function startSSEStream(runId) {
  if (activeEventSource) activeEventSource.close();

  const es = new EventSource(API.stream(runId));
  activeEventSource = es;

  es.addEventListener("progress", (e) => {
    const data = JSON.parse(e.data);
    $("#progress-bar-fill").style.width = `${data.percent}%`;
    appendLog(data.log || `[${data.percent}%] ${data.step}: ${data.message}`, "info");
  });

  es.addEventListener("status", (e) => {
    const data = JSON.parse(e.data);
    updateDrawerStatus(data.status);
    appendLog(`▶ ${data.message}`, "info");
  });

  es.addEventListener("done", (e) => {
    const data = JSON.parse(e.data);
    es.close();
    activeEventSource = null;

    if (data.status === "success") {
      $("#progress-bar-fill").style.width = "100%";
      updateDrawerStatus("success");
      showMetrics(data.metrics);
      toast(`Pipeline selesai! ${data.metrics?.rows_loaded ?? 0} baris dimuat.`, "success");
      appendLog("✓ Pipeline selesai dengan sukses.", "success");
    } else {
      updateDrawerStatus("error");
      toast(`Pipeline gagal: ${data.error}`, "error");
      appendLog(`✕ Error: ${data.error}`, "error");
    }

    // Refresh stats
    updateDashboardStats();
  });

  es.addEventListener("close", () => { es.close(); activeEventSource = null; });
  es.onerror = () => { es.close(); activeEventSource = null; };
}

function showMetrics(metrics) {
  if (!metrics) return;
  const container = $("#drawer-metrics");
  if (!container) return;
  container.innerHTML = `
    <div class="metrics-row">
      <div class="metric-box"><div class="metric-value">${metrics.rows_extracted ?? 0}</div><div class="metric-label">Extracted</div></div>
      <div class="metric-box"><div class="metric-value">${metrics.rows_transformed ?? 0}</div><div class="metric-label">Transformed</div></div>
      <div class="metric-box"><div class="metric-value">${metrics.rows_loaded ?? 0}</div><div class="metric-label">Loaded</div></div>
      <div class="metric-box"><div class="metric-value">${metrics.duration_seconds ?? 0}s</div><div class="metric-label">Duration</div></div>
    </div>
  `;
}

// ─── History ──────────────────────────────────────────────────────────────────

async function loadHistory() {
  const tbody = $("#history-tbody");
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:32px;color:var(--text-3)"><div class="spinner" style="margin:0 auto"></div></td></tr>`;

  try {
    const res = await fetch(API.history);
    const runs = await res.json();
    renderHistory(runs);
    updateStats(runs);
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;color:var(--red);padding:24px">Gagal memuat history.</td></tr>`;
  }
}

function renderHistory(runs) {
  const tbody = $("#history-tbody");
  if (!runs.length) {
    tbody.innerHTML = `<tr><td colspan="7">
      <div class="empty-state">
        <div class="empty-icon">🔄</div>
        <div class="empty-title">Belum ada pipeline</div>
        <div class="empty-desc">Jalankan pipeline pertama Anda dari halaman Pipeline Builder.</div>
      </div>
    </td></tr>`;
    return;
  }

  tbody.innerHTML = runs.map(r => `
    <tr>
      <td><code style="font-family:var(--mono);font-size:11px;color:var(--text-2)">${r.run_id}</code></td>
      <td style="font-weight:500">${r.pipeline_name}</td>
      <td><span class="connector-chip">${CONNECTOR_ICONS[r.source_type] || "🔌"} ${r.source_type}</span></td>
      <td><span class="connector-chip">${CONNECTOR_ICONS[r.destination_type] || "🔌"} ${r.destination_type}</span></td>
      <td>${statusPill(r.status)}</td>
      <td style="color:var(--text-2)">${r.metrics?.rows_loaded ?? "—"}</td>
      <td style="color:var(--text-3);font-size:12px">${formatDate(r.started_at)}</td>
    </tr>
  `).join("");
}

// ─── Dashboard Stats ──────────────────────────────────────────────────────────

async function updateDashboardStats() {
  try {
    const res = await fetch(API.history);
    const runs = await res.json();
    updateStats(runs);
  } catch (_) { /* ignore */ }
}

function updateStats(runs) {
  const total   = runs.length;
  const success = runs.filter(r => r.status === "success").length;
  const errors  = runs.filter(r => r.status === "error").length;
  const running = runs.filter(r => r.status === "running").length;
  const rate    = total > 0 ? Math.round((success / total) * 100) : 0;
  const last    = runs[0];

  setStatValue("stat-total",   total);
  setStatValue("stat-success", success);
  setStatValue("stat-error",   errors);
  setStatValue("stat-running", running);
  setStatValue("stat-rate",    `${rate}%`);
  setStatValue("stat-last",    last ? formatDate(last.started_at) : "—");
}

function setStatValue(id, value) {
  const el = $(`#${id}`);
  if (el) el.textContent = value;
}

// ─── Init ─────────────────────────────────────────────────────────────────────

async function init() {
  // Load registered connectors from API
  try {
    const res = await fetch(API.connectors);
    state.connectors = await res.json();
  } catch (err) {
    toast("Tidak dapat memuat daftar connector.", "error");
    state.connectors = {
      sources: ["csv", "json", "sqlite", "mysql", "postgresql"],
      destinations: ["csv", "json", "sqlite", "mysql", "postgresql"],
    };
  }

  // Navigation
  $$(".nav-item[data-view]").forEach(btn => {
    btn.addEventListener("click", () => showView(btn.dataset.view));
  });

  // Init builder
  initBuilder();

  // Drawer close
  $("#drawer-close-btn")?.addEventListener("click", closeProgressDrawer);
  $("#drawer-header")?.addEventListener("click", (e) => {
    if (!e.target.closest("button")) return;
  });

  // Initial view
  showView("dashboard");
  updateDashboardStats();
}

document.addEventListener("DOMContentLoaded", init);
