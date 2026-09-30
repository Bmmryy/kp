/* ===================================================================
   FlowETL — Vanilla JS Application
   No build step, no framework. ES2020+.
   =================================================================== */

// ─── Constants ───────────────────────────────────────────────────────────────

const API = {
  connectors:       "/api/connectors",
  run:              "/api/pipeline/run",
  status:           (id) => `/api/pipeline/status/${id}`,
  history:          "/api/pipeline/history",
  stream:           (id) => `/stream/${id}`,
  files:            "/api/files",
  download:         (path) => `/api/files/download?path=${encodeURIComponent(path)}`,
  installDb:        "/api/database/install-sql",
  schedules:        "/api/schedules",
  schedulesToggle:  (id) => `/api/schedules/${id}/toggle`,
  schedulesTrigger: (id) => `/api/schedules/${id}/trigger`,
  schedulesDelete:  (id) => `/api/schedules/${id}`,
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
    { key: "database",   label: "Database", type: "text",     placeholder: "HospitalManagementSystem", required: true },
    { key: "user",       label: "User",     type: "text",     placeholder: "root",        required: true },
    { key: "password",   label: "Password", type: "password", placeholder: "kosongkan jika tanpa password", required: false },
    { key: "table_name", label: "Table",    type: "text",     placeholder: "Department",  required: false },
  ],
  postgresql: [
    { key: "host",       label: "Host",     type: "text",     placeholder: "localhost",    required: true },
    { key: "port",       label: "Port",     type: "number",   placeholder: "5432",         required: false },
    { key: "database",   label: "Database", type: "text",     placeholder: "hospital_dw",  required: true },
    { key: "user",       label: "User",     type: "text",     placeholder: "postgres",     required: true },
    { key: "password",   label: "Password", type: "password", placeholder: "••••••••",     required: false },
    { key: "table_name", label: "Table",    type: "text",     placeholder: "patients_dim", required: false },
  ],
};
CONNECTOR_FIELDS.postgres = CONNECTOR_FIELDS.postgresql;

// SF Symbols-style SVG icons for each connector (no emoji)
function getConnectorSVG(name) {
  const s = `width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"`;
  const icons = {
    csv:        `<svg ${s}><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="8" y1="13" x2="16" y2="13"></line><line x1="8" y1="17" x2="16" y2="17"></line></svg>`,
    json:       `<svg ${s}><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>`,
    jsonl:      `<svg ${s}><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>`,
    sqlite:     `<svg ${s}><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path></svg>`,
    mysql:      `<svg ${s}><rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect><rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect><line x1="6" y1="6" x2="6.01" y2="6"></line><line x1="6" y1="18" x2="6.01" y2="18"></line></svg>`,
    postgresql: `<svg ${s}><rect x="3" y="4" width="18" height="16" rx="3"></rect><line x1="3" y1="10" x2="21" y2="10"></line><line x1="9" y1="20" x2="9" y2="10"></line></svg>`,
    postgres:   `<svg ${s}><rect x="3" y="4" width="18" height="16" rx="3"></rect><line x1="3" y1="10" x2="21" y2="10"></line><line x1="9" y1="20" x2="9" y2="10"></line></svg>`,
  };
  return icons[name] || `<svg ${s}><circle cx="12" cy="12" r="4"></circle><path d="M1.05 12H7M17 12h5.95M12 1.05V7M12 17v5.95"></path></svg>`;
}

const CONNECTOR_ICONS = Object.fromEntries(
  ["csv","json","jsonl","sqlite","mysql","postgresql","postgres"].map(k => [k, getConnectorSVG(k)])
);

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
  const svgCheck = `<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
  const svgX     = `<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;
  const svgSpin  = `<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.19"/></svg>`;
  const svgDot   = `<svg width="7" height="7" viewBox="0 0 8 8"><circle cx="4" cy="4" r="4" fill="currentColor"/></svg>`;
  const map = {
    success: [svgCheck + " Sukses",  "pill-success"],
    error:   [svgX     + " Error",   "pill-error"],
    running: [svgSpin  + " Berjalan","pill-running"],
    pending: [svgDot   + " Menunggu","pill-pending"],
  };
  const [text, cls] = map[status] || ["—", "pill-pending"];
  return `<span class="pill ${cls}" style="display:inline-flex;align-items:center;gap:5px">${text}</span>`;
}

// ─── Toast ───────────────────────────────────────────────────────────────────

function toast(message, type = "info", duration = 4000) {
  const container = $("#toast-container");
  const t = el("div", { class: `toast toast-${type}` });
  const svgOk   = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#34C759" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>`;
  const svgErr  = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#FF3B30" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`;
  const svgInfo = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#0071E3" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`;
  const icons = { success: svgOk, error: svgErr, info: svgInfo };
  t.innerHTML = `<span style="flex-shrink:0">${icons[type] || svgInfo}</span><span>${message}</span>`;
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
  const titles = {
    dashboard: "Dashboard",
    builder:   "Pipeline Builder",
    history:   "Pipeline History",
    files:     "File Data (Unduh / Install)",
    schedules: "Penjadwalan Otomatis",
  };
  $("#topbar-title").textContent = titles[name] || name;
  if (name === "history")   loadHistory();
  if (name === "dashboard") updateDashboardStats();
  if (name === "files")     loadFiles();
  if (name === "schedules") loadSchedules();
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
    }, `<span class="chip-icon">${icon}</span> <span class="chip-text">${name}</span>`);
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

function updateTransformBadge() {
  const badge = $("#transform-mode-badge");
  if (!badge) return;
  const count = [
    $("#transform-trim")?.checked,
    $("#transform-capitalize")?.checked,
    $("#transform-uppercase")?.checked,
    $("#transform-lowercase")?.checked,
    $("#transform-fill-null")?.checked,
    $("#transform-mask")?.checked,
  ].filter(Boolean).length;

  if (count === 0) {
    badge.className = "pill pill-pending";
    badge.textContent = "Pass-Through";
  } else {
    badge.className = "pill pill-success";
    badge.textContent = `${count} Transformasi Aktif`;
  }
}

function collectTransformations() {
  const transforms = [];
  if ($("#transform-trim")?.checked) {
    transforms.push({ type: "trim", params: {} });
  }
  if ($("#transform-capitalize")?.checked) {
    transforms.push({ type: "capitalize", params: { mode: "title" } });
  }
  if ($("#transform-uppercase")?.checked) {
    transforms.push({ type: "uppercase", params: {} });
  }
  if ($("#transform-lowercase")?.checked) {
    transforms.push({ type: "lowercase", params: {} });
  }
  if ($("#transform-fill-null")?.checked) {
    const val = $("#transform-fill-null-val")?.value || "N/A";
    transforms.push({ type: "fill_null", params: { default_value: val } });
  }
  if ($("#transform-mask")?.checked) {
    const cols = ($("#transform-mask-cols")?.value || "").split(",").map(c => c.trim()).filter(Boolean);
    transforms.push({ type: "mask", params: { columns: cols, mask_char: "*", keep_start: 3, keep_end: 3 } });
  }
  return transforms;
}

async function handleRunPipeline() {
  if (!state.selectedSource) { toast("Pilih Source connector terlebih dahulu.", "error"); return; }
  if (!state.selectedDestination) { toast("Pilih Destination connector terlebih dahulu.", "error"); return; }

  const srcOpts = collectOptions("source-fields", state.selectedSource);
  const dstOpts = collectOptions("dest-fields", state.selectedDestination);
  const transforms = collectTransformations();

  // Inject custom SQL query if mode is active
  const customSQLActive = $("#toggle-custom-sql")?.checked;
  if (customSQLActive) {
    const sql = $("#custom-sql-query")?.value?.trim();
    if (!sql) { toast("Tulis SQL Query terlebih dahulu.", "error"); return; }
    srcOpts.query = sql;
  }

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
        transformations: transforms,
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
  const dl = $("#drawer-download-btn");
  if (dl) dl.innerHTML = "";
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
      fetch(API.status(runId)).then(r => r.json()).then(info => {
        if (info.output_file) renderDownloadButton(info.output_file);
      }).catch(() => {});
    } else {
      updateDrawerStatus("error");
      toast(`Pipeline gagal: ${data.error}`, "error");
      appendLog(`✕ Error: ${data.error}`, "error");
    }

    // Refresh stats
    updateDashboardStats();
  });

  es.addEventListener("close", () => { es.close(); activeEventSource = null; });
  es.onerror = async () => {
    es.close();
    activeEventSource = null;
    // Fallback: cek status via API
    try {
      const res = await fetch(API.status(runId));
      if (res.ok) {
        const data = await res.json();
        if (data.status === "success") {
          $("#progress-bar-fill").style.width = "100%";
          updateDrawerStatus("success");
          showMetrics(data.metrics);
          if (data.output_file) renderDownloadButton(data.output_file);
          toast(`Pipeline selesai! ${data.metrics?.rows_loaded ?? 0} baris dimuat.`, "success");
          if ($("#log-console").children.length === 0 && data.log_lines) {
            data.log_lines.forEach(l => appendLog(l, "info"));
          }
          appendLog("✓ Pipeline selesai dengan sukses.", "success");
        } else if (data.status === "error") {
          updateDrawerStatus("error");
          toast(`Pipeline gagal: ${data.error_message}`, "error");
          if ($("#log-console").children.length === 0 && data.log_lines) {
            data.log_lines.forEach(l => appendLog(l, "error"));
          }
        }
        updateDashboardStats();
      }
    } catch (_) {}
  };
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

function renderDownloadButton(outputFile) {
  const btnContainer = $("#drawer-download-btn");
  if (!btnContainer) return;
  if (outputFile) {
    const filename = outputFile.split("/").pop();
    btnContainer.innerHTML = `
      <a href="${API.download(outputFile)}" download class="btn btn-primary"
         style="display:inline-flex;align-items:center;gap:8px;padding:10px 28px;font-size:13.5px;font-weight:600;text-decoration:none">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
          <polyline points="7 10 12 15 17 10"></polyline>
          <line x1="12" y1="15" x2="12" y2="3"></line>
        </svg>
        Unduh File Data (${filename})
      </a>
    `;
  } else {
    btnContainer.innerHTML = "";
  }
}

// ─── Files View (Unduh / Install Data) ────────────────────────────────────────

async function loadFiles() {
  const tbody = $("#files-tbody");
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:32px;color:var(--text-3)"><div class="spinner" style="margin:0 auto"></div></td></tr>`;

  try {
    const res = await fetch(API.files);
    const files = await res.json();
    if (!files.length) {
      tbody.innerHTML = `<tr><td colspan="5">
        <div class="empty-state">
          <div class="empty-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
            </svg>
          </div>
          <div class="empty-title">Belum ada file data</div>
          <div class="empty-desc">Jalankan pipeline dengan destination CSV, JSON, atau SQLite untuk menghasilkan file data.</div>
        </div>
      </td></tr>`;
      return;
    }

    tbody.innerHTML = files.map(f => `
      <tr>
        <td>
          <span style="display:inline-flex;align-items:center;gap:6px;font-weight:600">
            <span style="color:var(--text-secondary)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
              </svg>
            </span>
            ${f.name}
          </span>
        </td>
        <td><span class="pill pill-pending">${f.size_formatted}</span></td>
        <td style="color:var(--text-tertiary);font-size:12px">${f.modified}</td>
        <td><code style="font-family:var(--mono);font-size:11px;color:var(--text-secondary)">${f.path}</code></td>
        <td>
          <a href="${f.download_url}" download class="btn btn-secondary btn-sm" style="text-decoration:none;gap:6px">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
            Unduh
          </a>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:var(--red);padding:24px">Gagal memuat file.</td></tr>`;
  }
}

// ─── Schedules ────────────────────────────────────────────────────────────────

const FREQ_LABEL = {
  "30s":     "Setiap 30 Detik (Demo)",
  "1m":      "Setiap 1 Menit (Demo)",
  "5m":      "Setiap 5 Menit",
  "15m":     "Setiap 15 Menit",
  "hourly":  "Per Jam",
  "daily":   "Per Hari",
  "weekly":  "Per Minggu",
  "monthly": "Per Bulan",
};

async function loadSchedules() {
  const tbody = $("#schedules-tbody");
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:32px"><div class="spinner" style="margin:0 auto"></div></td></tr>`;
  try {
    const res  = await fetch(API.schedules);
    const jobs = await res.json();
    renderSchedules(jobs);
  } catch (_) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;color:var(--red);padding:24px">Gagal memuat jadwal.</td></tr>`;
  }
}

function renderSchedules(jobs) {
  const tbody = $("#schedules-tbody");
  if (!jobs.length) {
    tbody.innerHTML = `<tr><td colspan="8">
      <div class="empty-state">
        <div class="empty-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="16" y1="2" x2="16" y2="6"></line>
            <line x1="8" y1="2" x2="8" y2="6"></line>
            <line x1="3" y1="10" x2="21" y2="10"></line>
          </svg>
        </div>
        <div class="empty-title">Belum ada jadwal</div>
        <div class="empty-desc">Klik "Tambah Jadwal" untuk membuat ETL otomatis pertama Anda.</div>
      </div>
    </td></tr>`;
    return;
  }
  tbody.innerHTML = jobs.map(j => `
    <tr>
      <td style="font-weight:600">${j.name}</td>
      <td style="color:var(--text-secondary)">${j.pipeline_name}</td>
      <td>
        <span class="connector-chip" style="display:inline-flex;align-items:center;gap:5px;font-size:11px">
          ${j.source_type} <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg> ${j.dest_type}
        </span>
      </td>
      <td><span class="pill pill-pending">${FREQ_LABEL[j.frequency] || j.frequency}</span></td>
      <td>
        <label class="toggle-switch" title="${j.enabled ? 'Nonaktifkan' : 'Aktifkan'}">
          <input type="checkbox" ${j.enabled ? "checked" : ""} onchange="toggleSchedule('${j.id}', this)">
          <span class="toggle-slider"></span>
        </label>
      </td>
      <td style="color:var(--text-tertiary);font-size:12px">${j.last_run ? formatDate(j.last_run) : "—"}</td>
      <td style="color:var(--text-tertiary);font-size:12px">${j.next_run ? formatDate(j.next_run) : "—"}</td>
      <td style="display:flex;gap:6px;align-items:center">
        <button class="btn btn-secondary btn-sm" style="padding:4px 10px;font-size:12px" onclick="triggerScheduleNow('${j.id}')" title="Jalankan Sekarang">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
        </button>
        <button class="btn btn-sm" style="padding:4px 10px;font-size:12px;background:var(--red,#FF3B30);color:#fff;border:none;border-radius:8px" onclick="deleteSchedule('${j.id}')" title="Hapus Jadwal">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"></path><path d="M10 11v6"></path><path d="M14 11v6"></path></svg>
        </button>
      </td>
    </tr>
  `).join("");
}

async function toggleSchedule(id, checkbox) {
  try {
    const res = await fetch(API.schedulesToggle(id), { method: "PATCH" });
    if (!res.ok) throw new Error();
    const data = await res.json();
    toast(`Jadwal ${data.enabled ? "diaktifkan" : "dinonaktifkan"}.`, "success");
  } catch (_) {
    toast("Gagal mengubah status jadwal.", "error");
    checkbox.checked = !checkbox.checked; // revert
  }
}

async function triggerScheduleNow(id) {
  try {
    const res = await fetch(API.schedulesTrigger(id), { method: "POST" });
    if (!res.ok) throw new Error();
    toast("Pipeline dijadwalkan dijalankan sekarang!", "success");
  } catch (_) {
    toast("Gagal menjalankan jadwal.", "error");
  }
}

async function deleteSchedule(id) {
  if (!confirm("Hapus jadwal ini? Tindakan ini tidak dapat dibatalkan.")) return;
  try {
    const res = await fetch(API.schedulesDelete(id), { method: "DELETE" });
    if (!res.ok) throw new Error();
    toast("Jadwal dihapus.", "success");
    loadSchedules();
  } catch (_) {
    toast("Gagal menghapus jadwal.", "error");
  }
}

function showCreateScheduleModal() {
  const existing = $("#modal-create-schedule");
  if (existing) { existing.remove(); return; }

  const freqOptions = Object.entries(FREQ_LABEL).map(([v, l]) =>
    `<option value="${v}">${l}</option>`
  ).join("");

  const modal = document.createElement("div");
  modal.id = "modal-create-schedule";
  modal.style.cssText = `
    position:fixed;inset:0;z-index:9999;display:flex;align-items:center;justify-content:center;
    background:rgba(0,0,0,0.35);backdrop-filter:blur(6px);
  `;
  modal.innerHTML = `
    <div style="background:#fff;border-radius:18px;padding:32px;width:520px;max-width:95vw;box-shadow:0 24px 64px rgba(0,0,0,0.18);animation:fadeInUp .22s ease">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px">
        <h2 style="font-size:17px;font-weight:700;margin:0">Tambah Jadwal ETL</h2>
        <button onclick="document.getElementById('modal-create-schedule').remove()" style="background:none;border:none;cursor:pointer;padding:4px">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
      </div>

      <div style="display:grid;gap:14px">
        <div class="form-group" style="margin:0">
          <label class="form-label">Nama Jadwal</label>
          <input class="form-input" id="sc-name" placeholder="Sinkronisasi Harian Pasien" style="width:100%;box-sizing:border-box">
        </div>
        <div class="form-group" style="margin:0">
          <label class="form-label">Nama Pipeline</label>
          <input class="form-input" id="sc-pipeline" placeholder="daily_sync" style="width:100%;box-sizing:border-box">
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
          <div class="form-group" style="margin:0">
            <label class="form-label">Tipe Source</label>
            <input class="form-input" id="sc-src-type" placeholder="mysql" style="width:100%;box-sizing:border-box">
          </div>
          <div class="form-group" style="margin:0">
            <label class="form-label">Tipe Destination</label>
            <input class="form-input" id="sc-dst-type" placeholder="csv" style="width:100%;box-sizing:border-box">
          </div>
        </div>
        <div class="form-group" style="margin:0">
          <label class="form-label">Source Options (JSON)</label>
          <textarea class="form-input" id="sc-src-opts" rows="3" style="width:100%;box-sizing:border-box;font-family:var(--mono);font-size:12px;resize:vertical" placeholder='{"host":"localhost","user":"root","password":"","database":"MyDB","table":"patients"}'></textarea>
        </div>
        <div class="form-group" style="margin:0">
          <label class="form-label">Destination Options (JSON)</label>
          <textarea class="form-input" id="sc-dst-opts" rows="2" style="width:100%;box-sizing:border-box;font-family:var(--mono);font-size:12px;resize:vertical" placeholder='{"path":"output/patients_daily.csv"}'></textarea>
        </div>
        <div class="form-group" style="margin:0">
          <label class="form-label">Frekuensi</label>
          <select class="form-input" id="sc-freq" style="width:100%;box-sizing:border-box">${freqOptions}</select>
        </div>
      </div>

      <div style="display:flex;gap:10px;justify-content:flex-end;margin-top:24px">
        <button class="btn btn-secondary" onclick="document.getElementById('modal-create-schedule').remove()">Batal</button>
        <button class="btn btn-primary" onclick="submitCreateSchedule()">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
          Buat Jadwal
        </button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
  modal.addEventListener("click", (e) => { if (e.target === modal) modal.remove(); });
  setTimeout(() => document.getElementById("sc-name")?.focus(), 50);
}

async function submitCreateSchedule() {
  const name     = $("#sc-name")?.value.trim();
  const pipeline = $("#sc-pipeline")?.value.trim();
  const srcType  = $("#sc-src-type")?.value.trim();
  const dstType  = $("#sc-dst-type")?.value.trim();
  const freq     = $("#sc-freq")?.value;
  let srcOpts, dstOpts;

  if (!name || !pipeline || !srcType || !dstType) {
    toast("Lengkapi semua field yang wajib diisi.", "error"); return;
  }

  try { srcOpts = JSON.parse($("#sc-src-opts")?.value || "{}"); }
  catch (_) { toast("Source Options bukan JSON valid.", "error"); return; }
  try { dstOpts = JSON.parse($("#sc-dst-opts")?.value || "{}"); }
  catch (_) { toast("Destination Options bukan JSON valid.", "error"); return; }

  try {
    const res = await fetch(API.schedules, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name, pipeline_name: pipeline,
        source_type: srcType, source_options: srcOpts,
        dest_type: dstType, dest_options: dstOpts,
        frequency: freq,
      }),
    });
    if (!res.ok) { const err = await res.json(); throw new Error(err.detail || "Error"); }
    toast(`Jadwal "${name}" berhasil dibuat!`, "success");
    $("#modal-create-schedule")?.remove();
    loadSchedules();
  } catch (e) {
    toast(`Gagal membuat jadwal: ${e.message}`, "error");
  }
}

// ─── Custom SQL Mode Toggle ────────────────────────────────────────────────────

function toggleCustomSQLMode(enabled) {
  const singleBlock = $("#source-single-table");
  const sqlBlock    = $("#source-custom-sql");
  if (singleBlock) singleBlock.style.display = enabled ? "none" : "";
  if (sqlBlock)    sqlBlock.style.display    = enabled ? "" : "none";
}



// ─── Database Install (1-Click) ──────────────────────────────────────────────

async function installHospitalDatabase() {
  const btn = $("#btn-install-db");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<div class="spinner"></div> Menginstall...`;
  }
  toast("Sedang menginstall database HospitalManagementSystem ke MySQL...", "info", 8000);

  try {
    const res = await fetch(API.installDb, { method: "POST" });
    const data = await res.json();
    if (res.ok) {
      toast(data.message || "Database berhasil di-install!", "success", 6000);
      updateDashboardStats();
    } else {
      toast(data.detail || "Gagal menginstall database.", "error");
    }
  } catch (e) {
    toast(`Error: ${e.message}`, "error");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg> Install Database`;
    }
  }
}

// ─── History ──────────────────────────────────────────────────────────────────

async function loadHistory() {
  const tbody = $("#history-tbody");
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:32px;color:var(--text-3)"><div class="spinner" style="margin:0 auto"></div></td></tr>`;

  try {
    const res = await fetch(API.history);
    const runs = await res.json();
    renderHistory(runs);
    updateStats(runs);
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;color:var(--red);padding:24px">Gagal memuat history.</td></tr>`;
  }
}

function renderHistory(runs) {
  const tbody = $("#history-tbody");
  if (!runs.length) {
    tbody.innerHTML = `<tr><td colspan="8">
      <div class="empty-state">
        <div class="empty-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="23 4 23 10 17 10"></polyline>
            <polyline points="1 20 1 14 7 14"></polyline>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
          </svg>
        </div>
        <div class="empty-title">Belum ada pipeline</div>
        <div class="empty-desc">Jalankan pipeline pertama Anda dari halaman Pipeline Builder.</div>
      </div>
    </td></tr>`;
    return;
  }

  tbody.innerHTML = runs.map(r => `
    <tr>
      <td><code style="font-family:var(--mono);font-size:11px;color:var(--text-secondary)">${r.run_id}</code></td>
      <td style="font-weight:500">${r.pipeline_name}</td>
      <td><span class="connector-chip" style="display:inline-flex;align-items:center;gap:6px">${CONNECTOR_ICONS[r.source_type] || getConnectorSVG(r.source_type)} <span>${r.source_type}</span></span></td>
      <td><span class="connector-chip" style="display:inline-flex;align-items:center;gap:6px">${CONNECTOR_ICONS[r.destination_type] || getConnectorSVG(r.destination_type)} <span>${r.destination_type}</span></span></td>
      <td>${statusPill(r.status)}</td>
      <td style="color:var(--text-secondary)">${r.metrics?.rows_loaded ?? "—"}</td>
      <td style="color:var(--text-tertiary);font-size:12px">${formatDate(r.started_at)}</td>
      <td>
        ${r.output_file ? `
          <a href="${API.download(r.output_file)}" download class="btn btn-secondary btn-sm"
             style="padding:4px 10px;font-size:12px;text-decoration:none;display:inline-flex;align-items:center;gap:5px">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
            Unduh
          </a>` : '<span style="color:var(--text-tertiary)">—</span>'}
      </td>
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
