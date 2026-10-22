/* ===================================================================
   FlowETL — Vanilla JS Application
   No build step, no framework. ES2020+.
   =================================================================== */

// ─── Constants ───────────────────────────────────────────────────────────────

const API = {
  connectors:       "/api/connectors",
  run:              "/api/pipeline/run",
  multiRun:         "/api/pipeline/multi-run",
  upload:           "/api/upload",
  verifyConn:       "/api/connector/verify",
  listDatabases:    "/api/connector/databases",
  listTables:       "/api/connector/tables",
  listColumns:      "/api/connector/columns",
  status:           (id) => `/api/pipeline/status/${id}`,
  history:          "/api/pipeline/history",
  stream:           (id) => `/stream/${id}`,
  files:            "/api/files",
  download:         (path) => `/api/files/download?path=${encodeURIComponent(path)}`,
  downloadZip:      (id) => `/api/pipeline/download-zip/${id}`,
  installDb:        "/api/database/install-sql",
  schedules:        "/api/schedules",
  schedulesGet:     (id) => `/api/schedules/${id}`,
  schedulesUpdate:  (id) => `/api/schedules/${id}`,
  schedulesToggle:  (id) => `/api/schedules/${id}/toggle`,
  schedulesTrigger: (id) => `/api/schedules/${id}/trigger`,
  schedulesDelete:  (id) => `/api/schedules/${id}`,
};

// Connector field definitions (what options each connector needs)
const CONNECTOR_FIELDS = {
  csv: [
    { key: "path",      label: "File Path",  type: "text",   placeholder: "data/dataset.csv", required: true },
    { key: "delimiter", label: "Delimiter",  type: "text",   placeholder: ",",                required: false },
    { key: "encoding",  label: "Encoding",   type: "text",   placeholder: "utf-8",            required: false },
  ],
  excel: [
    { key: "path",       label: "File Path (.xlsx)", type: "text", placeholder: "output/report.xlsx", required: true },
    { key: "sheet_name", label: "Sheet Name",        type: "text", placeholder: "Sheet1",             required: false },
  ],
  xlsx: [
    { key: "path",       label: "File Path (.xlsx)", type: "text", placeholder: "output/report.xlsx", required: true },
    { key: "sheet_name", label: "Sheet Name",        type: "text", placeholder: "Sheet1",             required: false },
  ],
  json: [
    { key: "path", label: "File Path", type: "text", placeholder: "data/dataset.json", required: true },
  ],
  jsonl: [
    { key: "path", label: "File Path (JSONL)", type: "text", placeholder: "data/events.jsonl", required: true },
  ],
  sqlite: [
    { key: "path",       label: "Database Path", type: "text", placeholder: "data/database.sqlite", required: true },
    { key: "table_name", label: "Table Name",     type: "text", placeholder: "analytics_data",       required: false },
  ],
  mysql: [
    { key: "host",       label: "Host",     type: "text",     placeholder: "localhost",     required: true },
    { key: "port",       label: "Port",     type: "number",   placeholder: "3306",          required: false },
    { key: "database",   label: "Database", type: "text",     placeholder: "production_db", required: true },
    { key: "user",       label: "User",     type: "text",     placeholder: "root",          required: true },
    { key: "password",   label: "Password", type: "password", placeholder: "kosongkan jika tanpa password", required: false },
    { key: "table_name", label: "Table",    type: "text",     placeholder: "users",         required: false },
  ],
  postgresql: [
    { key: "host",       label: "Host",     type: "text",     placeholder: "localhost",    required: true },
    { key: "port",       label: "Port",     type: "number",   placeholder: "5432",         required: false },
    { key: "database",   label: "Database", type: "text",     placeholder: "analytics_dw", required: true },
    { key: "user",       label: "User",     type: "text",     placeholder: "postgres",     required: true },
    { key: "password",   label: "Password", type: "password", placeholder: "••••••••",     required: false },
    { key: "table_name", label: "Table",    type: "text",     placeholder: "dim_users",    required: false },
  ],
  oracle: [
    { key: "host",         label: "Host",         type: "text",     placeholder: "localhost",   required: true },
    { key: "port",         label: "Port",         type: "number",   placeholder: "1521",        required: false },
    { key: "service_name", label: "Service Name", type: "text",     placeholder: "FREEPDB1",    required: true },
    { key: "database",     label: "Schema/Owner", type: "text",     placeholder: "SYSTEM",      required: true },
    { key: "user",         label: "User",         type: "text",     placeholder: "system",      required: true },
    { key: "password",     label: "Password",     type: "password", placeholder: "••••••••",    required: false },
    { key: "table_name",   label: "Table",        type: "text",     placeholder: "CUSTOMERS",   required: false },
  ],
};
CONNECTOR_FIELDS.postgres = CONNECTOR_FIELDS.postgresql;

function getDbDefaultPort(dbtype) {
  if (dbtype === "mysql") return 3306;
  if (dbtype === "oracle") return 1521;
  return 5432;
}

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
    oracle:     `<svg ${s}><rect x="2" y="4" width="20" height="16" rx="2"></rect><path d="M7 15h10M7 9h10"></path></svg>`,
  };
  return icons[name] || `<svg ${s}><circle cx="12" cy="12" r="4"></circle><path d="M1.05 12H7M17 12h5.95M12 1.05V7M12 17v5.95"></path></svg>`;
}

const CONNECTOR_ICONS = Object.fromEntries(
  ["csv","json","jsonl","sqlite","mysql","postgresql","postgres","oracle"].map(k => [k, getConnectorSVG(k)])
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

  // Builder v2 state
  srcCategory: "file",        // "file" | "sql"
  srcFileFormat: "csv",       // "csv" | "json" | "jsonl" | "sqlite"
  srcDbType: "mysql",         // "mysql" | "postgresql"
  srcUploadedFiles: [],       // [{file_id, original_name, saved_name, path, size_formatted}]
  srcDbCards: [],             // [{id, verified, host, port, user, password, database, tables:[]}]
  srcDbCardCounter: 0,

  dstCategory: "file",        // "file" | "sql"
  dstFileFormat: "csv",       // "csv" | "json" | "jsonl" | "sqlite"
  dstDbType: "mysql",
  dstVerified: false,
  dstDatabases: [],

  // Column Selection & Mapping State (Single DB / Table focus)
  srcColumns: [],             // [{name, type, nullable, primary_key}]
  srcSelectedColumns: [],     // ["colA", "colB"]
  srcSelectedTable: "",       // table name selected
  dstTableMode: "existing",   // "existing" | "new"
  dstAvailableTables: [],     // existing tables in target DB
  dstSelectedTable: "",       // target table name
  dstColumns: [],             // columns of target table
  columnMapping: {},          // { [source_col]: target_col }

  // Per-column transformation rules
  columnTransformRules: [],   // [{ id, column, type, params: {} }]
  ruleCounter: 0,
  transformTab: "rules",      // "rules" | "global"

  dstLoadMode: "sync",        // "sync" | "append" | "truncate"
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
  // Pipeline name
  const nameInput = $("#pipeline-name-input");
  if (nameInput) {
    nameInput.value = state.pipelineName;
    nameInput.addEventListener("input", () => { state.pipelineName = nameInput.value || "My Pipeline"; });
  }

  // Run button
  const runBtn = $("#run-pipeline-btn");
  if (runBtn) runBtn.addEventListener("click", handleRunPipeline);

  // Init upload drop zone
  initDropZone();

  // Render initial transform rules (empty state)
  renderColumnTransformRules();
}

function setTransformTab(tab) {
  state.transformTab = tab;
  $("#transform-tab-rules")?.classList.toggle("selected", tab === "rules");
  $("#transform-tab-global")?.classList.toggle("selected", tab === "global");
  const rSec = $("#transform-rules-section");
  const gSec = $("#transform-global-section");
  if (rSec) rSec.style.display = tab === "rules" ? "" : "none";
  if (gSec) gSec.style.display = tab === "global" ? "" : "none";
}

function addColumnTransformRule() {
  const availableCols = state.srcSelectedColumns.length
    ? state.srcSelectedColumns
    : state.srcColumns.map(c => c.name);

  const defaultCol = availableCols[0] || "";
  const ruleId = ++state.ruleCounter;
  state.columnTransformRules.push({
    id: ruleId,
    column: defaultCol,
    type: "uppercase",
    params: {
      fill_null_val: "N/A",
      mask_char: "*",
      keep_start: 2,
      keep_end: 2,
    }
  });

  renderColumnTransformRules();
  updateTransformBadge();
}

function removeColumnTransformRule(id) {
  state.columnTransformRules = state.columnTransformRules.filter(r => r.id !== id);
  renderColumnTransformRules();
  updateTransformBadge();
}

function updateColumnTransformRule(id, field, value) {
  const rule = state.columnTransformRules.find(r => r.id === id);
  if (!rule) return;
  rule[field] = value;
  renderColumnTransformRules();
  updateTransformBadge();
}

function updateRuleParam(id, paramKey, paramVal) {
  const rule = state.columnTransformRules.find(r => r.id === id);
  if (!rule) return;
  if (!rule.params) rule.params = {};
  rule.params[paramKey] = paramVal;
}

function renderColumnTransformRules() {
  const container = $("#column-transform-rules-list");
  if (!container) return;

  const availableCols = state.srcSelectedColumns.length
    ? state.srcSelectedColumns
    : state.srcColumns.map(c => c.name);

  if (!state.columnTransformRules.length) {
    container.innerHTML = `
      <div style="font-size:11.5px;color:var(--text-tertiary);padding:14px;background:var(--bg-canvas);border-radius:8px;text-align:center;border:1px dashed var(--border)">
        Belum ada aturan transformasi per kolom.<br>
        <span style="font-size:10.5px">Klik <strong>+ Tambah Aturan</strong> di atas untuk menentukan kolom &amp; jenis transformasinya.</span>
      </div>
    `;
    return;
  }

  container.innerHTML = state.columnTransformRules.map(rule => {
    if (!rule.column && availableCols.length) {
      rule.column = availableCols[0];
    }

    const isFillNull = rule.type === "fill_null";
    const isMask = rule.type === "mask";

    return `
      <div class="transform-rule-item" id="rule-item-${rule.id}">
        <div class="transform-rule-row">
          <select class="form-select transform-rule-col-select" onchange="updateColumnTransformRule(${rule.id}, 'column', this.value)">
            ${availableCols.length ? availableCols.map(c => `
              <option value="${c}" ${c === rule.column ? 'selected' : ''}>${c}</option>
            `).join("") : `<option value="">(Pilih tabel sumber dulu)</option>`}
          </select>
          <span class="transform-rule-arrow">──►</span>
          <select class="form-select transform-rule-type-select" onchange="updateColumnTransformRule(${rule.id}, 'type', this.value)">
            <option value="uppercase" ${rule.type === 'uppercase' ? 'selected' : ''}>UPPERCASE (Kapital)</option>
            <option value="lowercase" ${rule.type === 'lowercase' ? 'selected' : ''}>lowercase (Kecil)</option>
            <option value="capitalize" ${rule.type === 'capitalize' ? 'selected' : ''}>Capitalize (Title Case)</option>
            <option value="trim" ${rule.type === 'trim' ? 'selected' : ''}>Trim (Hapus Spasi)</option>
            <option value="fill_null" ${rule.type === 'fill_null' ? 'selected' : ''}>Fill Null (Isi Kosong)</option>
            <option value="mask" ${rule.type === 'mask' ? 'selected' : ''}>Sensor (Masking)</option>
          </select>
          <button type="button" class="transform-rule-remove-btn" onclick="removeColumnTransformRule(${rule.id})" title="Hapus aturan ini">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>

        ${isFillNull ? `
          <div class="transform-rule-extra">
            <span>Nilai default:</span>
            <input type="text" class="form-control" style="flex:1" value="${rule.params?.fill_null_val || 'N/A'}" oninput="updateRuleParam(${rule.id}, 'fill_null_val', this.value)">
          </div>
        ` : ""}

        ${isMask ? `
          <div class="transform-rule-extra" style="flex-wrap:wrap">
            <span>Karakter:</span>
            <input type="text" class="form-control" style="width:36px;text-align:center" value="${rule.params?.mask_char || '*'}" oninput="updateRuleParam(${rule.id}, 'mask_char', this.value)">
            <span>Depan:</span>
            <input type="number" class="form-control" style="width:48px;text-align:center" value="${rule.params?.keep_start ?? 2}" oninput="updateRuleParam(${rule.id}, 'keep_start', this.value)">
            <span>Belakang:</span>
            <input type="number" class="form-control" style="width:48px;text-align:center" value="${rule.params?.keep_end ?? 2}" oninput="updateRuleParam(${rule.id}, 'keep_end', this.value)">
          </div>
        ` : ""}
      </div>
    `;
  }).join("");
}

function updateTransformBadge() {
  const badge = $("#transform-mode-badge");
  if (!badge) return;
  const globalCount = [
    $("#transform-trim")?.checked,
    $("#transform-capitalize")?.checked,
    $("#transform-uppercase")?.checked,
    $("#transform-lowercase")?.checked,
    $("#transform-fill-null")?.checked,
    $("#transform-mask")?.checked,
  ].filter(Boolean).length;

  const ruleCount = (state.columnTransformRules || []).length;
  const totalCount = globalCount + ruleCount;

  if (totalCount === 0) {
    badge.className = "pill pill-pending";
    badge.textContent = "Pass-Through";
  } else {
    badge.className = "pill pill-success";
    badge.textContent = `${totalCount} Operasi Aktif`;
  }
}

function collectTransformations() {
  const transforms = [];

  // 1. Per-column transformation rules
  for (const rule of (state.columnTransformRules || [])) {
    if (!rule.column) continue;
    if (rule.type === "uppercase") {
      transforms.push({ type: "uppercase", params: { columns: [rule.column] } });
    } else if (rule.type === "lowercase") {
      transforms.push({ type: "lowercase", params: { columns: [rule.column] } });
    } else if (rule.type === "capitalize") {
      transforms.push({ type: "capitalize", params: { mode: "title", columns: [rule.column] } });
    } else if (rule.type === "trim") {
      transforms.push({ type: "trim", params: { columns: [rule.column] } });
    } else if (rule.type === "fill_null") {
      const val = rule.params?.fill_null_val || "N/A";
      transforms.push({ type: "fill_null", params: { default_value: val, columns: [rule.column] } });
    } else if (rule.type === "mask") {
      transforms.push({
        type: "mask",
        params: {
          columns: [rule.column],
          mask_char: rule.params?.mask_char || "*",
          keep_start: parseInt(rule.params?.keep_start ?? 2),
          keep_end: parseInt(rule.params?.keep_end ?? 2),
        }
      });
    }
  }

  // 2. Global transformations
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
  if ($("#transform-filter")?.checked) {
    const col = $("#transform-filter-col")?.value.trim();
    const op  = $("#transform-filter-op")?.value;
    const val = $("#transform-filter-val")?.value.trim();
    if (col && op && val !== "") {
      const numVal = (!isNaN(val) && val !== "") ? (val.includes(".") ? parseFloat(val) : parseInt(val, 10)) : val;
      transforms.push({ type: "filter", params: { filters: [{ column: col, operator: op, value: numVal }] } });
    }
  }
  return transforms;
}

async function handleRunPipeline() {
  // Collect sources & destination from new UI
  const sources = collectSources();
  const dest    = collectDestination();

  if (!sources || sources.length === 0) {
    if (state.srcCategory === "file") {
      toast("Upload minimal 1 file terlebih dahulu.", "error");
    } else {
      toast("Verifikasi koneksi, pilih database & tabel terlebih dahulu.", "error");
    }
    return;
  }
  if (!dest) {
    if (state.dstCategory === "sql") {
      toast("Verifikasi koneksi destination, pilih database & nama tabel baru.", "error");
    } else {
      toast("Lengkapi konfigurasi destination terlebih dahulu.", "error");
    }
    return;
  }

  const transforms = collectTransformations();
  const name       = state.pipelineName || "My Pipeline";

  // Safety confirmation for destructive load modes
  const ifExists = dest.options?.if_exists || "append";
  if (ifExists === "replace") {
    const ok = confirm(`⚠️ PERINGATAN LOAD MODE (REPLACE):\n\nOperasi ini akan MENGHAPUS (DROP) tabel tujuan jika sudah ada dan membuat ulang dari awal.\n\nLanjutkan eksekusi?`);
    if (!ok) return;
  } else if (ifExists === "truncate") {
    const ok = confirm(`⚠️ PERINGATAN LOAD MODE (TRUNCATE):\n\nOperasi ini akan MENGOSONGKAN (DELETE SEMUA DATA) pada tabel tujuan sebelum mengisi data baru.\n\nLanjutkan eksekusi?`);
    if (!ok) return;
  } else if (ifExists === "sync" || ifExists === "mirror") {
    const ok = confirm(`⚡ KONFIRMASI MODE SINKRONISASI (AUTO-SYNC / MIRROR):\n\nData pada tabel tujuan akan diselaraskan agar persis sama dengan sumber. Data lama di tujuan yang tidak ada di sumber akan dibersihkan.\n\nLanjutkan sinkronisasi?`);
    if (!ok) return;
  }

  // Attach Column Selection or Column Mapping
  if (state.dstTableMode === "existing" && state.dstSelectedTable && state.dstColumns.length > 0) {
    const activeMapping = {};
    const seenDst = {};
    for (const srcCol of state.srcSelectedColumns) {
      const dstCol = state.columnMapping[srcCol];
      if (dstCol && dstCol !== "__ignore__") {
        const dstLower = dstCol.toLowerCase();
        if (seenDst[dstLower]) {
          toast(`Pemetaan kolom tidak valid: Dua kolom sumber ('${seenDst[dstLower]}' dan '${srcCol}') dipetakan ke kolom target yang sama '${dstCol}'. Ubah pemetaan agar setiap kolom tujuan unik.`, "error", 6000);
          return;
        }
        seenDst[dstLower] = srcCol;
        activeMapping[srcCol] = dstCol;
      }
    }
    if (Object.keys(activeMapping).length === 0) {
      toast("Perhatian: Belum ada kolom sumber yang dipetakan ke tabel tujuan. Silakan petakan minimal satu kolom tujuan pada kotak Pemetaan Kolom.", "error", 5000);
      return;
    }
    transforms.push({
      type: "column_mapping",
      params: {
        mapping: activeMapping,
        drop_unmapped: true,
        target_table: state.dstSelectedTable,
      },
    });
  } else if (state.srcSelectedColumns.length > 0 && state.srcColumns.length > 0 && state.srcSelectedColumns.length < state.srcColumns.length) {
    transforms.push({
      type: "select_columns",
      params: {
        columns: state.srcSelectedColumns,
      },
    });
  }

  const runBtn = $("#run-pipeline-btn");
  if (runBtn) { runBtn.disabled = true; runBtn.innerHTML = `<div class="spinner"></div> Memulai...`; }

  try {
    const body = {
      pipeline_name: name,
      sources,
      destination_type: dest.type,
      destination_options: dest.options,
      transformations: transforms,
    };

    const res = await fetch(API.multiRun, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) {
      toast(data.detail || "Terjadi kesalahan.", "error");
      return;
    }

    state.currentRunId = data.run_id;
    toast(`Pipeline dikirim! ${sources.length} sumber → ${dest.type}. run_id: ${data.run_id}`, "info");
    openProgressDrawer(data.run_id);
    startSSEStream(data.run_id);

  } catch (err) {
    toast(`Error: ${err.message}`, "error");
  } finally {
    if (runBtn) {
      runBtn.disabled = false;
      runBtn.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg> Jalankan Pipeline`;
    }
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

function formatDisplayError(msg) {
  if (!msg) return "Terjadi kesalahan pada pipeline.";
  let str = String(msg);
  // Strip raw SQL and bound parameter dumps
  str = str.replace(/\[SQL:[\s\S]*?\]/g, "");
  str = str.replace(/\[parameters:[\s\S]*?\]/g, "");
  str = str.replace(/\(Background on this error at:[\s\S]*?\)/g, "");
  str = str.replace(/\(pymysql\.err\.\w+\)/g, "");
  str = str.replace(/\(psycopg2\.\w+\)/g, "");
  str = str.replace(/\(sqlite3\.\w+\)/g, "");
  return str.trim();
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

        const dlBtn = $("#drawer-download-btn");
        if (dlBtn) {
          dlBtn.innerHTML = "";
          // Tombol download jika ada output file
          if (data.output_file) {
            renderDownloadButton(data.output_file);
          }
          // Tombol buat task berikutnya
          const nextBtn = document.createElement("button");
          nextBtn.className = "btn btn-primary btn-sm";
          nextBtn.style.cssText = "margin-top:10px;display:inline-flex;align-items:center;gap:6px";
          nextBtn.onclick = () => { closeProgressDrawer(); resetTaskBuilder(); };
          nextBtn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg> + Buat Task Berikutnya`;
          dlBtn.appendChild(nextBtn);
        }
    } else {
      updateDrawerStatus("error");
      const cleanErr = formatDisplayError(data.error);
      toast(`Pipeline gagal: ${cleanErr}`, "error");
      appendLog(`✕ Error: ${cleanErr}`, "error");

      // Tombol Tutup & Coba Lagi agar user tidak terjebak
      const dlBtn = $("#drawer-download-btn");
      if (dlBtn) {
        dlBtn.innerHTML = `
          <button class="btn btn-secondary btn-sm" onclick="closeProgressDrawer()" style="margin-top:10px;display:inline-flex;align-items:center;gap:6px">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            Tutup &amp; Coba Lagi
          </button>
        `;
      }
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
          const cleanErr = formatDisplayError(data.error_message);
          toast(`Pipeline gagal: ${cleanErr}`, "error");
          if ($("#log-console").children.length === 0 && data.log_lines) {
            data.log_lines.forEach(l => appendLog(formatDisplayError(l), "error"));
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
  tbody.innerHTML = jobs.map(j => {
    const dstOpts = j.destination_options || j.dest_options || {};
    const mode = dstOpts.if_exists || "sync";
    const modeLabel = {
      sync: "⚡ Auto-Sync (Mirror)",
      append: "➕ Append Data",
      truncate: "🔄 Truncate & Reload",
    }[mode] || mode;

    return `
    <tr>
      <td style="font-weight:600">
        <div>${j.name}</div>
        <div style="margin-top:4px">
          <span class="pill ${mode === 'sync' ? 'pill-success' : 'pill-pending'}" style="font-size:10.5px;padding:2px 7px" title="Mode Sinkronisasi: ${modeLabel}">
            ${modeLabel}
          </span>
        </div>
      </td>
      <td style="color:var(--text-secondary)">${j.pipeline_name}</td>
      <td>
        <span class="connector-chip" style="display:inline-flex;align-items:center;gap:5px;font-size:11px">
          ${j.source_type} <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg> ${j.destination_type || j.dest_type || '—'}
        </span>
      </td>
      <td><span class="pill pill-pending">${FREQ_LABEL[j.frequency] || j.frequency}</span></td>
      <td>
        <label class="toggle-switch" title="${(j.is_enabled ?? j.enabled) ? 'Nonaktifkan' : 'Aktifkan'}">
          <input type="checkbox" ${(j.is_enabled ?? j.enabled) ? "checked" : ""} onchange="toggleSchedule('${j.id}', this)">
          <span class="toggle-slider"></span>
        </label>
      </td>
      <td style="color:var(--text-tertiary);font-size:12px">${(j.last_run_at || j.last_run) ? formatDate(j.last_run_at || j.last_run) : "—"}</td>
      <td style="color:var(--text-tertiary);font-size:12px">${(j.next_run_at || j.next_run) ? formatDate(j.next_run_at || j.next_run) : "—"}</td>
      <td style="display:flex;gap:6px;align-items:center">
        <button class="btn btn-secondary btn-sm" style="padding:4px 10px;font-size:12px" onclick="triggerScheduleNow('${j.id}')" title="Jalankan Sekarang">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
        </button>
        <button class="btn btn-secondary btn-sm" style="padding:4px 10px;font-size:12px" onclick="editSchedule('${j.id}')" title="Edit Jadwal">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 20h9"></path>
            <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
          </svg>
        </button>
        <button class="btn btn-sm" style="padding:4px 10px;font-size:12px;background:var(--red,#FF3B30);color:#fff;border:none;border-radius:8px" onclick="deleteSchedule('${j.id}')" title="Hapus Jadwal">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"></path><path d="M10 11v6"></path><path d="M14 11v6"></path></svg>
        </button>
      </td>
    </tr>
    `;
  }).join("");
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
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || "Server menolak pemicuan jadwal.");
    }
    const data = await res.json().catch(() => ({}));
    const runId = data.run_id;

    if (runId) {
      // Open progress drawer to show real-time execution
      state.currentRunId = runId;
      openProgressDrawer(runId);
      startSSEStream(runId);
      toast(`✓ Jadwal dipicu! Memantau eksekusi...`, "success");
    } else {
      toast(`✓ Jadwal berhasil dipicu! ${data.message || "Pipeline sedang berjalan di background."}`, "success");
    }
    // Reload schedules to update next_run / last_run status
    setTimeout(loadSchedules, 1200);
  } catch (err) {
    toast(`Gagal menjalankan jadwal: ${err.message || "Terjadi kesalahan sistem."}`, "error");
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

function showCreateScheduleModal(prefillRun = null, editJob = null) {
  const existing = $("#modal-create-schedule");
  if (existing) { existing.remove(); return; }

  const freqOptions = Object.entries(FREQ_LABEL).map(([v, l]) =>
    `<option value="${v}">${l}</option>`
  ).join("");

  const srcTypeOptions = ["mysql", "postgresql", "oracle", "csv", "json", "jsonl", "sqlite"].map(t =>
    `<option value="${t}">${t.toUpperCase()}</option>`
  ).join("");
  const dstTypeOptions = ["csv", "json", "jsonl", "sqlite", "mysql", "postgresql", "oracle"].map(t =>
    `<option value="${t}">${t.toUpperCase()}</option>`
  ).join("");

  const modal = document.createElement("div");
  modal.id = "modal-create-schedule";
  modal.style.cssText = `
    position:fixed;inset:0;z-index:9999;display:flex;align-items:center;justify-content:center;
    background:rgba(0,0,0,0.45);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);
  `;
  modal.innerHTML = `
    <div style="background:var(--surface);color:var(--text);border:1px solid var(--border);border-radius:18px;padding:32px;width:580px;max-width:96vw;max-height:90vh;overflow-y:auto;box-shadow:var(--shadow-xl);animation:fadeInUp .22s ease">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
        <div>
          <h2 style="font-size:17px;font-weight:700;margin:0;color:var(--text)">${editJob ? "Edit Jadwal ETL" : "Tambah Jadwal ETL"}</h2>
          <div style="font-size:12px;color:var(--text-tertiary);margin-top:2px">
            ${editJob ? `Perbarui parameter, koneksi, atau frekuensi jadwal "${editJob.name}"` : "Jadwalkan task berdasarkan riwayat atau task yang pernah dijalankan"}
          </div>
        </div>
        <button onclick="document.getElementById('modal-create-schedule').remove()" style="background:none;border:none;cursor:pointer;padding:4px;color:var(--text-secondary)">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
      </div>

      <!-- Pilih dari Riwayat Pipeline / Task (hanya jika mode tambah baru) -->
      <div class="form-group full-width" style="margin-bottom:16px;background:var(--surface-secondary);padding:12px 14px;border-radius:10px;border:1px solid var(--border);${editJob ? 'display:none;' : ''}">
        <label class="form-label" style="font-size:12px;font-weight:600;margin-bottom:6px;display:flex;align-items:center;gap:6px">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
          Pilih Task dari Riwayat yang Pernah Dijalankan
        </label>
        <select class="form-select" id="sc-history-picker" onchange="onSelectHistoryForSchedule(this.value)" style="font-size:12.5px;background:var(--surface);color:var(--text);border:1px solid var(--border)">
          <option value="">— Pilih task dari riwayat untuk mengisi otomatis form —</option>
        </select>
      </div>

      <div class="sc-modal-grid">
        <div class="form-group full-width" style="margin:0">
          <label class="form-label">Nama Jadwal</label>
          <input class="form-control" id="sc-name" placeholder="Sinkronisasi Harian Data Produksi" style="width:100%;box-sizing:border-box">
        </div>
        <div class="form-group full-width" style="margin:0">
          <label class="form-label">Nama Pipeline</label>
          <input class="form-control" id="sc-pipeline" placeholder="daily_data_sync" style="width:100%;box-sizing:border-box">
        </div>

        <div class="form-group" style="margin:0">
          <label class="form-label">Tipe Source</label>
          <select class="form-select" id="sc-src-type" onchange="onScSrcTypeChange(this.value)">${srcTypeOptions}</select>
        </div>
        <div class="form-group" style="margin:0">
          <label class="form-label">Tipe Destination</label>
          <select class="form-select" id="sc-dst-type" onchange="onScDstTypeChange(this.value)">${dstTypeOptions}</select>
        </div>

        <!-- Source SQL fields (shown when SQL type selected) -->
        <div id="sc-src-sql-fields" class="form-group full-width" style="margin:0;display:none">
          <label class="form-label">Koneksi Source Database</label>
          <div style="display:grid;grid-template-columns:1fr 80px;gap:8px;margin-bottom:6px">
            <input class="form-control" id="sc-src-host" type="text" placeholder="localhost">
            <input class="form-control" id="sc-src-port" type="number" placeholder="3306">
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px">
            <input class="form-control" id="sc-src-user" type="text" placeholder="root">
            <input class="form-control" id="sc-src-pass" type="password" placeholder="password">
          </div>
          <input class="form-control" id="sc-src-database" type="text" placeholder="Nama database (contoh: production_db)" style="margin-bottom:6px;width:100%;box-sizing:border-box">
          <input class="form-control" id="sc-src-table" type="text" placeholder="Nama tabel (contoh: users)" style="width:100%;box-sizing:border-box">
        </div>

        <!-- Source File fields (shown when file type selected) -->
        <div id="sc-src-file-fields" class="form-group full-width" style="margin:0">
          <label class="form-label">Path File Source</label>
          <input class="form-control" id="sc-src-path" type="text" placeholder="data/dataset.csv" style="width:100%;box-sizing:border-box">
        </div>

        <!-- Destination SQL fields -->
        <div id="sc-dst-sql-fields" class="form-group full-width" style="margin:0;display:none">
          <label class="form-label">Koneksi Destination Database</label>
          <div style="display:grid;grid-template-columns:1fr 80px;gap:8px;margin-bottom:6px">
            <input class="form-control" id="sc-dst-host" type="text" placeholder="localhost">
            <input class="form-control" id="sc-dst-port" type="number" placeholder="3306">
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px">
            <input class="form-control" id="sc-dst-user" type="text" placeholder="root">
            <input class="form-control" id="sc-dst-pass" type="password" placeholder="password">
          </div>
          <input class="form-control" id="sc-dst-database" type="text" placeholder="Nama database tujuan" style="margin-bottom:6px;width:100%;box-sizing:border-box">
          <input class="form-control" id="sc-dst-table" type="text" placeholder="Nama tabel tujuan" style="width:100%;box-sizing:border-box">
        </div>

        <!-- Destination File fields -->
        <div id="sc-dst-file-fields" class="form-group full-width" style="margin:0">
          <label class="form-label">Path File Output</label>
          <input class="form-control" id="sc-dst-path" type="text" placeholder="output/daily_export.csv" style="width:100%;box-sizing:border-box">
        </div>

        <div class="form-group full-width" style="margin:0">
          <label class="form-label">Frekuensi Jadwal</label>
          <select class="form-select" id="sc-freq">${freqOptions}</select>
        </div>

        <!-- Pilihan Khusus Sinkronisasi & Auto Schema Evolution -->
        <div class="form-group full-width" style="margin:0;background:var(--surface-secondary);border:1px solid var(--border);padding:14px;border-radius:12px">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
            <label style="font-size:12.5px;font-weight:700;color:var(--text);display:flex;align-items:center;gap:6px;margin:0">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--primary,#0071E3)" stroke-width="2.5"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
              Pilihan Khusus Sinkronisasi &amp; Schema Evolution
            </label>
            <span class="pill pill-success" style="font-size:10px;padding:2px 8px">Bisa Diedit Bebas</span>
          </div>

          <div style="font-size:11.5px;color:var(--text-secondary);margin-bottom:8px">
            Atur bagaimana database tujuan merespons setiap kali ada update data atau perubahan kolom di tabel sumber (misal update via phpMyAdmin):
          </div>

          <select class="form-select" id="sc-load-mode" style="font-size:12.5px;font-weight:600;background:var(--surface);color:var(--text);border:1px solid var(--border);margin-bottom:8px">
            <option value="sync">⚡ Sync / Mirror — Selalu Sinkron Otomatis (Data &amp; Struktur Kolom Mengikuti Sumber)</option>
            <option value="append">➕ Append — Tambah Data Baru (Otomatis Tambah Kolom Baru)</option>
            <option value="truncate">🔄 Truncate &amp; Reload — Kosongkan lalu Muat Ulang Data Terbaru</option>
          </select>

          <label style="display:flex;align-items:center;gap:8px;cursor:pointer;font-size:12px;color:var(--text)">
            <input type="checkbox" id="sc-auto-evolution" checked style="accent-color:var(--accent,#0071E3)">
            <span><strong>Auto-Alter Struktur:</strong> Otomatis buat tabel baru &amp; tambah kolom baru (<code>ALTER TABLE</code>) jika ada update di sumber.</span>
          </label>
        </div>
      </div>

      <div style="display:flex;gap:10px;justify-content:flex-end;margin-top:24px">
        <button class="btn btn-secondary" onclick="document.getElementById('modal-create-schedule').remove()">Batal</button>
        ${editJob ? `
          <button class="btn btn-primary" onclick="submitUpdateSchedule('${editJob.id}')">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
              <polyline points="17 21 17 13 7 13 7 21"></polyline>
              <polyline points="7 3 7 8 15 8"></polyline>
            </svg>
            Simpan Perubahan
          </button>
        ` : `
          <button class="btn btn-primary" onclick="submitCreateSchedule()">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
            Buat Jadwal
          </button>
        `}
      </div>
    </div>
  `;
  document.body.appendChild(modal);
  modal.addEventListener("click", (e) => { if (e.target === modal) modal.remove(); });

  if (editJob) {
    applyJobToScheduleForm(editJob);
  } else {
    // Load history runs into dropdown
    populateScheduleHistoryDropdown(prefillRun);
  }
  setTimeout(() => document.getElementById("sc-name")?.focus(), 50);
}

// Global cache for runs loaded in modal
let _cachedHistoryRuns = [];

async function populateScheduleHistoryDropdown(prefillRun = null) {
  const sel = $("#sc-history-picker");
  if (!sel) return;

  try {
    const res = await fetch(API.history);
    const runs = await res.json();
    _cachedHistoryRuns = runs || [];

    if (!runs || runs.length === 0) {
      sel.innerHTML = `<option value="">(Belum ada riwayat task/pipeline yang pernah dijalankan)</option>`;
      return;
    }

    sel.innerHTML = `<option value="">— Pilih task dari riwayat (${runs.length} riwayat ditemukan) —</option>` +
      runs.map((r, idx) => {
        const timeStr = r.started_at ? formatDate(r.started_at) : "";
        const label = `${r.pipeline_name} [${r.source_type} ──► ${r.destination_type}] (${r.status === 'success' ? 'Sukses' : r.status}) ${timeStr ? '- ' + timeStr : ''}`;
        return `<option value="${r.run_id}">${label}</option>`;
      }).join("");

    if (prefillRun) {
      sel.value = prefillRun.run_id;
      applyRunToScheduleForm(prefillRun);
    }
  } catch (err) {
    sel.innerHTML = `<option value="">Gagal memuat riwayat: ${err.message}</option>`;
  }
}

function onSelectHistoryForSchedule(runId) {
  if (!runId) return;
  const run = _cachedHistoryRuns.find(r => r.run_id === runId);
  if (!run) return;
  applyRunToScheduleForm(run);
}

function applyRunToScheduleForm(run) {
  if (!run) return;

  // 1. Nama Jadwal & Pipeline
  const nameEl = $("#sc-name");
  const pipeEl = $("#sc-pipeline");
  if (nameEl) nameEl.value = `Jadwal: ${run.pipeline_name}`;
  if (pipeEl) pipeEl.value = run.pipeline_name;

  // 2. Source Configuration
  const srcTypeSelect = $("#sc-src-type");
  const rawSrcType = run.source_type || "";
  const cleanSrcType = rawSrcType.split("+")[0]; // handle multi-source label
  if (srcTypeSelect && cleanSrcType) {
    srcTypeSelect.value = cleanSrcType;
    onScSrcTypeChange(cleanSrcType);

    const isSrcSql = ["mysql", "postgresql", "postgres", "oracle"].includes(cleanSrcType);
    const srcOpts = run.source_options || (run.sources && run.sources[0]?.options) || {};
    if (isSrcSql) {
      if ($("#sc-src-host")) $("#sc-src-host").value = srcOpts.host || "localhost";
      if ($("#sc-src-port")) $("#sc-src-port").value = srcOpts.port || getDbDefaultPort(cleanSrcType);
      if ($("#sc-src-user")) $("#sc-src-user").value = srcOpts.user || "root";
      if ($("#sc-src-pass")) $("#sc-src-pass").value = srcOpts.password || "";
      if ($("#sc-src-database")) $("#sc-src-database").value = srcOpts.database || "";
      if ($("#sc-src-table")) $("#sc-src-table").value = srcOpts.table_name || srcOpts.table || "";
    } else {
      if ($("#sc-src-path")) $("#sc-src-path").value = srcOpts.path || "";
    }
  }

  // 3. Destination Configuration
  const dstTypeSelect = $("#sc-dst-type");
  const dstType = run.destination_type || "csv";
  if (dstTypeSelect && dstType) {
    dstTypeSelect.value = dstType;
    onScDstTypeChange(dstType);

    const isDstSql = ["mysql", "postgresql", "postgres", "oracle"].includes(dstType);
    const dstOpts = run.destination_options || {};
    if (isDstSql) {
      if ($("#sc-dst-host")) $("#sc-dst-host").value = dstOpts.host || "localhost";
      if ($("#sc-dst-port")) $("#sc-dst-port").value = dstOpts.port || getDbDefaultPort(dstType);
      if ($("#sc-dst-user")) $("#sc-dst-user").value = dstOpts.user || "root";
      if ($("#sc-dst-pass")) $("#sc-dst-pass").value = dstOpts.password || "";
      if ($("#sc-dst-database")) $("#sc-dst-database").value = dstOpts.database || "";
      if ($("#sc-dst-table")) $("#sc-dst-table").value = dstOpts.table_name || dstOpts.table || "";
    } else {
      if ($("#sc-dst-path")) $("#sc-dst-path").value = dstOpts.path || "";
    }
    if (dstOpts.if_exists && $("#sc-load-mode")) {
      $("#sc-load-mode").value = dstOpts.if_exists;
    }
    if ($("#sc-auto-evolution")) {
      $("#sc-auto-evolution").checked = (dstOpts.auto_schema_evolution !== false);
    }
  }

  toast(`Form terisi otomatis dari riwayat task: "${run.pipeline_name}"`, "info");
}

function applyJobToScheduleForm(job) {
  if (!job) return;

  const nameEl = $("#sc-name");
  const pipeEl = $("#sc-pipeline");
  if (nameEl) nameEl.value = job.name || "";
  if (pipeEl) pipeEl.value = job.pipeline_name || "";

  const srcTypeSelect = $("#sc-src-type");
  const srcType = job.source_type || "csv";
  if (srcTypeSelect) {
    srcTypeSelect.value = srcType;
    onScSrcTypeChange(srcType);

    const isSrcSql = ["mysql", "postgresql", "postgres", "oracle"].includes(srcType);
    const srcOpts = job.source_options || {};
    if (isSrcSql) {
      if ($("#sc-src-host")) $("#sc-src-host").value = srcOpts.host || "localhost";
      if ($("#sc-src-port")) $("#sc-src-port").value = srcOpts.port || getDbDefaultPort(srcType);
      if ($("#sc-src-user")) $("#sc-src-user").value = srcOpts.user || "root";
      if ($("#sc-src-pass")) $("#sc-src-pass").value = srcOpts.password || "";
      if ($("#sc-src-database")) $("#sc-src-database").value = srcOpts.database || "";
      if ($("#sc-src-table")) $("#sc-src-table").value = srcOpts.table_name || srcOpts.table || "";
    } else {
      if ($("#sc-src-path")) $("#sc-src-path").value = srcOpts.path || "";
    }
  }

  const dstTypeSelect = $("#sc-dst-type");
  const dstType = job.destination_type || job.dest_type || "csv";
  if (dstTypeSelect) {
    dstTypeSelect.value = dstType;
    onScDstTypeChange(dstType);

    const isDstSql = ["mysql", "postgresql", "postgres", "oracle"].includes(dstType);
    const dstOpts = job.destination_options || job.dest_options || {};
    if (isDstSql) {
      if ($("#sc-dst-host")) $("#sc-dst-host").value = dstOpts.host || "localhost";
      if ($("#sc-dst-port")) $("#sc-dst-port").value = dstOpts.port || getDbDefaultPort(dstType);
      if ($("#sc-dst-user")) $("#sc-dst-user").value = dstOpts.user || "root";
      if ($("#sc-dst-pass")) $("#sc-dst-pass").value = dstOpts.password || "";
      if ($("#sc-dst-database")) $("#sc-dst-database").value = dstOpts.database || "";
      if ($("#sc-dst-table")) $("#sc-dst-table").value = dstOpts.table_name || dstOpts.table || "";
    } else {
      if ($("#sc-dst-path")) $("#sc-dst-path").value = dstOpts.path || "";
    }
  }

  const freqEl = $("#sc-freq");
  if (freqEl && job.frequency) {
    freqEl.value = job.frequency;
  }
  const loadModeEl = $("#sc-load-mode");
  const jobLoadMode = (job.destination_options && job.destination_options.if_exists) || "sync";
  if (loadModeEl) loadModeEl.value = jobLoadMode;
  const autoEvoEl = $("#sc-auto-evolution");
  if (autoEvoEl) {
    autoEvoEl.checked = (job.destination_options && job.destination_options.auto_schema_evolution !== false);
  }
}

function onScSrcTypeChange(val) {
  const isSql  = ["mysql","postgresql","postgres","oracle"].includes(val);
  const sqlFld = $("#sc-src-sql-fields");
  const filFld = $("#sc-src-file-fields");
  if (sqlFld)  sqlFld.style.display = isSql ? "" : "none";
  if (filFld)  filFld.style.display = isSql ? "none" : "";
  // Update port placeholder
  const portInp = $("#sc-src-port");
  if (portInp) portInp.placeholder = String(getDbDefaultPort(val));
}

function onScDstTypeChange(val) {
  const isSql  = ["mysql","postgresql","postgres","oracle"].includes(val);
  const sqlFld = $("#sc-dst-sql-fields");
  const filFld = $("#sc-dst-file-fields");
  if (sqlFld)  sqlFld.style.display = isSql ? "" : "none";
  if (filFld)  filFld.style.display = isSql ? "none" : "";
  const portInp = $("#sc-dst-port");
  if (portInp) portInp.placeholder = String(getDbDefaultPort(val));
}

function getScheduleFormData() {
  const name     = $("#sc-name")?.value.trim();
  const pipeline = $("#sc-pipeline")?.value.trim();
  const srcType  = $("#sc-src-type")?.value;
  const dstType  = $("#sc-dst-type")?.value;
  const freq     = $("#sc-freq")?.value;

  if (!name || !pipeline || !srcType || !dstType) {
    toast("Lengkapi semua field yang wajib diisi.", "error"); return null;
  }

  // Build source options based on type
  let srcOpts = {};
  const isSrcSql = ["mysql","postgresql","postgres","oracle"].includes(srcType);
  if (isSrcSql) {
    srcOpts = {
      host:     $("#sc-src-host")?.value.trim() || "localhost",
      port:     parseInt($("#sc-src-port")?.value) || getDbDefaultPort(srcType),
      user:     $("#sc-src-user")?.value.trim() || "root",
      password: $("#sc-src-pass")?.value || "",
      database: $("#sc-src-database")?.value.trim(),
      table_name: $("#sc-src-table")?.value.trim(),
    };
    if (!srcOpts.database) { toast("Database source wajib diisi.", "error"); return null; }
    if (!srcOpts.table_name) { toast("Tabel source wajib diisi.", "error"); return null; }
  } else {
    srcOpts = { path: $("#sc-src-path")?.value.trim() };
    if (!srcOpts.path) { toast("Path file source wajib diisi.", "error"); return null; }
  }

  // Build destination options based on type
  let dstOpts = {};
  const isDstSql = ["mysql","postgresql","postgres","oracle"].includes(dstType);
  if (isDstSql) {
    dstOpts = {
      host:     $("#sc-dst-host")?.value.trim() || "localhost",
      port:     parseInt($("#sc-dst-port")?.value) || getDbDefaultPort(dstType),
      user:     $("#sc-dst-user")?.value.trim() || "root",
      password: $("#sc-dst-pass")?.value || "",
      database: $("#sc-dst-database")?.value.trim(),
      table_name: $("#sc-dst-table")?.value.trim(),
    };
    if (!dstOpts.database) { toast("Database destination wajib diisi.", "error"); return null; }
    if (!dstOpts.table_name) { toast("Tabel destination wajib diisi.", "error"); return null; }
  } else {
    dstOpts = { path: $("#sc-dst-path")?.value.trim() };
    if (!dstOpts.path) { toast("Path file destination wajib diisi.", "error"); return null; }
  }

  dstOpts.if_exists = $("#sc-load-mode")?.value || "sync";
  dstOpts.auto_schema_evolution = $("#sc-auto-evolution")?.checked !== false;

  return {
    name,
    pipeline_name: pipeline,
    source_type: srcType,
    source_options: srcOpts,
    destination_type: dstType,
    destination_options: dstOpts,
    frequency: freq,
  };
}

async function submitCreateSchedule() {
  const payload = getScheduleFormData();
  if (!payload) return;

  try {
    const res = await fetch(API.schedules, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json();
      let msg = "Terjadi kesalahan.";
      if (typeof err.detail === "string") {
        msg = err.detail;
      } else if (Array.isArray(err.detail)) {
        msg = err.detail.map(d => `${d.loc ? d.loc.slice(1).join('.') : ''}: ${d.msg}`).join("; ");
      } else if (err.message) {
        msg = err.message;
      }
      throw new Error(msg);
    }
    toast(`Jadwal "${payload.name}" berhasil dibuat!`, "success");
    $("#modal-create-schedule")?.remove();
    loadSchedules();
  } catch (e) {
    toast(`Gagal membuat jadwal: ${e.message}`, "error");
  }
}

async function submitUpdateSchedule(id) {
  const payload = getScheduleFormData();
  if (!payload) return;

  try {
    const res = await fetch(API.schedulesUpdate(id), {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json();
      let msg = "Terjadi kesalahan.";
      if (typeof err.detail === "string") {
        msg = err.detail;
      } else if (Array.isArray(err.detail)) {
        msg = err.detail.map(d => `${d.loc ? d.loc.slice(1).join('.') : ''}: ${d.msg}`).join("; ");
      } else if (err.message) {
        msg = err.message;
      }
      throw new Error(msg);
    }
    toast(`Jadwal "${payload.name}" berhasil diperbarui!`, "success");
    $("#modal-create-schedule")?.remove();
    loadSchedules();
  } catch (e) {
    toast(`Gagal memperbarui jadwal: ${e.message}`, "error");
  }
}

async function editSchedule(id) {
  try {
    const res = await fetch(API.schedulesGet(id));
    if (!res.ok) throw new Error("Jadwal tidak ditemukan.");
    const job = await res.json();
    showCreateScheduleModal(null, job);
  } catch (err) {
    toast(`Gagal memuat jadwal: ${err.message}`, "error");
  }
}

// ─── Schedule Current Task (Pre-fills from active Task Builder) ───────────────

function scheduleCurrentTask() {
  const sources = collectSources();
  const dest    = collectDestination();
  const taskName = $("#pipeline-name-input")?.value.trim() || state.pipelineName || "Task Baru";

  if (!sources || sources.length === 0) {
    toast("Pilih sumber data terlebih dahulu sebelum menjadwalkan task.", "error");
    return;
  }
  if (!dest) {
    toast("Lengkapi konfigurasi tujuan (destination) terlebih dahulu.", "error");
    return;
  }

  // Tampilkan modal jadwal
  showCreateScheduleModal();

  setTimeout(() => {
    // 1. Isi nama jadwal dan pipeline berdasarkan nama task
    const nameEl = $("#sc-name");
    const pipeEl = $("#sc-pipeline");
    if (nameEl) nameEl.value = `Jadwal: ${taskName}`;
    if (pipeEl) pipeEl.value = taskName;

    // 2. Pre-fill Source
    const src = sources[0];
    const srcTypeSelect = $("#sc-src-type");
    if (srcTypeSelect && src.type) {
      srcTypeSelect.value = src.type;
      onScSrcTypeChange(src.type);

      const isSrcSql = ["mysql", "postgresql", "postgres", "oracle"].includes(src.type);
      if (isSrcSql) {
        if ($("#sc-src-host")) $("#sc-src-host").value = src.options.host || "localhost";
        if ($("#sc-src-port")) $("#sc-src-port").value = src.options.port || getDbDefaultPort(src.type);
        if ($("#sc-src-user")) $("#sc-src-user").value = src.options.user || "root";
        if ($("#sc-src-pass")) $("#sc-src-pass").value = src.options.password || "";
        if ($("#sc-src-database")) $("#sc-src-database").value = src.options.database || "";
        if ($("#sc-src-table")) $("#sc-src-table").value = src.options.table_name || src.options.table || "";
      } else {
        if ($("#sc-src-path")) $("#sc-src-path").value = src.options.path || "";
      }
    }

    // 3. Pre-fill Destination
    const dstTypeSelect = $("#sc-dst-type");
    if (dstTypeSelect && dest.type) {
      dstTypeSelect.value = dest.type;
      onScDstTypeChange(dest.type);

      const isDstSql = ["mysql", "postgresql", "postgres", "oracle"].includes(dest.type);
      if (isDstSql) {
        if ($("#sc-dst-host")) $("#sc-dst-host").value = dest.options.host || "localhost";
        if ($("#sc-dst-port")) $("#sc-dst-port").value = dest.options.port || getDbDefaultPort(dest.type);
        if ($("#sc-dst-user")) $("#sc-dst-user").value = dest.options.user || "root";
        if ($("#sc-dst-pass")) $("#sc-dst-pass").value = dest.options.password || "";
        if ($("#sc-dst-database")) $("#sc-dst-database").value = dest.options.database || "";
        if ($("#sc-dst-table")) $("#sc-dst-table").value = dest.options.table_name || dest.options.table || "";
      } else {
        if ($("#sc-dst-path")) $("#sc-dst-path").value = dest.options.path || "";
      }
      if ($("#sc-load-mode")) {
        $("#sc-load-mode").value = dest.options.if_exists || state.dstLoadMode || "sync";
      }
    }

    toast(`Form penjadwalan terisi otomatis dari "${taskName}"!`, "info");
  }, 60);
}

// ─── Custom SQL Mode Toggle ────────────────────────────────────────────────────

function toggleCustomSQLMode(enabled) {
  const singleBlock = $("#source-single-table");
  const sqlBlock    = $("#source-custom-sql");
  if (singleBlock) singleBlock.style.display = enabled ? "none" : "";
  if (sqlBlock)    sqlBlock.style.display    = enabled ? "" : "none";
}



// ─── Pipeline Builder v2 ─────────────────────────────────────────────────────

// ── SOURCE: Category switch (File / SQL) ────────────────────────────────────
function setSrcCategory(cat) {
  state.srcCategory = cat;
  $("#src-cat-file")?.classList.toggle("selected", cat === "file");
  $("#src-cat-sql")?.classList.toggle("selected", cat === "sql");
  $("#src-panel-file").style.display = cat === "file" ? "" : "none";
  $("#src-panel-sql").style.display  = cat === "sql"  ? "" : "none";
  // Auto-add first DB card when switching to SQL
  if (cat === "sql" && state.srcDbCards.length === 0) {
    addSrcDbCard();
  }
}

function selectSrcFileFormat(fmt) {
  state.srcFileFormat = fmt;
  $$("[data-fmt]", $("#src-file-format-group")).forEach(btn => {
    btn.classList.toggle("selected", btn.dataset.fmt === fmt);
  });
  // Show/hide format-specific options
  const csvOpts    = $("#src-csv-options");
  const sqliteOpts = $("#src-sqlite-options");
  const fileInput  = $("#src-file-input");
  if (csvOpts)    csvOpts.style.display    = fmt === "csv"    ? "" : "none";
  if (sqliteOpts) sqliteOpts.style.display = fmt === "sqlite" ? "" : "none";
  // Update accepted file types
  const acceptMap = { csv: ".csv", excel: ".xlsx,.xls", xlsx: ".xlsx,.xls", json: ".json", jsonl: ".jsonl", sqlite: ".sqlite,.db" };
  if (fileInput) fileInput.accept = acceptMap[fmt] || "";
  // Re-detect columns if files already uploaded
  if (state.srcUploadedFiles.length > 0) detectFileColumns();
}


function selectSrcDbType(dbtype) {
  state.srcDbType = dbtype;
  $$("[data-dbtype]", $("#src-panel-sql")).forEach(btn => {
    btn.classList.toggle("selected", btn.dataset.dbtype === dbtype);
  });
  // Update default port hints for existing cards
  $$(".src-db-port-input").forEach(inp => {
    inp.placeholder = String(getDbDefaultPort(dbtype));
  });
}

// ── SOURCE: File Upload ─────────────────────────────────────────────────────
function handleSrcFileSelect(files) {
  if (!files || files.length === 0) return;
  const zone  = $("#src-drop-zone");
  const list  = $("#src-file-list");
  if (zone)  zone.classList.add("dragover");
  uploadFilesToServer(Array.from(files)).then(async uploaded => {
    uploaded.forEach(f => { state.srcUploadedFiles.push(f); });
    renderUploadedFiles();
    if (zone) zone.classList.remove("dragover");
    toast(`${uploaded.length} file berhasil diupload.`, "success");

    // Auto-detect columns from the first uploaded file
    await detectFileColumns();
  }).catch(err => {
    toast(`Upload gagal: ${err.message}`, "error");
    if (zone) zone.classList.remove("dragover");
  });
}

async function detectFileColumns() {
  const container = $("#src-file-columns-container");
  if (!container) return;

  if (state.srcUploadedFiles.length === 0) {
    container.style.display = "none";
    container.innerHTML = "";
    state.srcColumns = [];
    state.srcSelectedColumns = [];
    return;
  }

  // Use first file for column detection
  const firstFile = state.srcUploadedFiles[0];
  const fmt = state.srcFileFormat || "csv";

  try {
    const q = new URLSearchParams({ type: fmt, path: firstFile.path });
    const res = await fetch(`${API.listColumns}?${q}`);
    if (!res.ok) throw new Error("Gagal memuat kolom file");
    const data = await res.json();
    const cols = data.columns || [];

    state.srcColumns = cols;
    state.srcSelectedColumns = cols.map(c => c.name);

    if (cols.length === 0) {
      container.style.display = "none";
      container.innerHTML = "";
      return;
    }

    const TYPE_OPTIONS = ["string","integer","float","decimal","boolean","date","datetime","time","json","binary"];

    container.style.display = "block";
    container.innerHTML = `
      <div class="column-checklist-box">
        <div class="column-checklist-header">
          <div class="column-checklist-title">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
            Kolom Terdeteksi (${cols.length})
          </div>
          <div style="display:flex;gap:6px">
            <button type="button" class="btn btn-secondary btn-sm" style="padding:2px 8px;font-size:10.5px" onclick="toggleAllSourceCols(true)">Pilih Semua</button>
            <button type="button" class="btn btn-secondary btn-sm" style="padding:2px 8px;font-size:10.5px" onclick="toggleAllSourceCols(false)">Kosongkan</button>
          </div>
        </div>
        <div class="column-checklist-grid">
          ${cols.map((col, idx) => `
            <label class="column-check-item">
              <div style="display:flex;align-items:center;gap:6px">
                <input type="checkbox" value="${col.name}" checked onchange="toggleSourceColumn('${col.name.replace(/'/g, "\\'")}', this.checked)">
                <span style="font-weight:500">${col.name}</span>
              </div>
              <select class="column-type-select" onchange="overrideSrcColumnType(${idx}, this.value)" title="Override tipe data kolom '${col.name}'">
                ${TYPE_OPTIONS.map(t => `<option value="${t}" ${(col.type||'string')===t?'selected':''}>${t}</option>`).join('')}
              </select>
            </label>
          `).join("")}
        </div>
        <div style="font-size:11px;color:var(--text-tertiary);margin-top:6px">
          Centang kolom yang ingin dikirim. Klik dropdown tipe untuk mengubah tipe data sebelum dimuat ke SQL.
        </div>
      </div>
    `;
    renderColumnMapping();
  } catch (e) {
    container.style.display = "none";
    console.warn("Gagal deteksi kolom file:", e.message);
  }
}

function overrideSrcColumnType(idx, newType) {
  if (state.srcColumns[idx]) {
    state.srcColumns[idx] = { ...state.srcColumns[idx], type: newType };
  }
}



async function uploadFilesToServer(files) {
  const formData = new FormData();
  files.forEach(f => formData.append("files", f));
  const res = await fetch(API.upload, { method: "POST", body: formData });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload error" }));
    throw new Error(err.detail || "Upload gagal");
  }
  return res.json();
}

function renderUploadedFiles() {
  const list = $("#src-file-list");
  if (!list) return;
  if (state.srcUploadedFiles.length === 0) {
    list.innerHTML = "";
    return;
  }
  list.innerHTML = state.srcUploadedFiles.map((f, i) => `
    <div class="upload-file-item">
      <span class="file-icon">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
      </span>
      <span class="file-name">${f.original_name}</span>
      <span class="file-size">${f.size_formatted}</span>
      <button class="file-remove" onclick="removeSrcFile(${i})" title="Hapus">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
      </button>
    </div>
  `).join("");
}

function removeSrcFile(index) {
  state.srcUploadedFiles.splice(index, 1);
  renderUploadedFiles();
  detectFileColumns();
}


// ── SOURCE: SQL DB Cards ────────────────────────────────────────────────────

async function verifySrcCard(id) {
  const card = state.srcDbCards.find(c => c.id === id);
  if (!card) return;

  const host     = $(`#src-host-${id}`)?.value.trim() || "";
  const port     = parseInt($(`#src-port-${id}`)?.value) || getDbDefaultPort(state.srcDbType);
  const user     = $(`#src-user-${id}`)?.value.trim() || "";
  const password = $(`#src-pass-${id}`)?.value || "";

  if (!host || !user) { toast("Host dan User wajib diisi.", "error"); return; }

  card.host = host; card.port = port; card.user = user; card.password = password;

  const btn   = $(`#src-verify-btn-${id}`);
  const msgEl = $(`#src-verify-msg-${id}`);
  if (btn)   { btn.classList.add("loading"); btn.disabled = true; }
  if (msgEl) msgEl.textContent = "Menghubungkan...";

  try {
    // 1. Verify — POST body flat (sesuai ConnectParams)
    const vRes = await fetch(API.verifyConn, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type: state.srcDbType, host, port, user, password }),
    });
    const vData = await vRes.json();
    if (!vData.ok) throw new Error(vData.error || "Koneksi gagal");

    // 2. List databases — GET dengan query params
    const params = new URLSearchParams({ type: state.srcDbType, host, port, user, password });
    const dbRes  = await fetch(`${API.listDatabases}?${params}`);
    if (!dbRes.ok) { const e = await dbRes.json(); throw new Error(e.detail || "Gagal load database"); }
    const dbData = await dbRes.json();

    card._databases = dbData.databases || [];
    card.verified   = true;
    card._connOpts  = { host, port, user, password };

    if (btn)   { btn.classList.remove("loading"); btn.classList.add("verified"); btn.disabled = false; btn.innerHTML = "✓ Terverifikasi"; }
    if (msgEl) { msgEl.style.color = "var(--success)"; msgEl.textContent = `${card._databases.length} database ditemukan`; }
    renderSrcDbCards();
  } catch (err) {
    card.verified = false;
    if (btn)   { btn.classList.remove("loading"); btn.classList.add("failed"); btn.disabled = false; btn.innerHTML = "✗ Gagal"; }
    if (msgEl) { msgEl.style.color = "var(--danger)"; msgEl.textContent = `Gagal: ${err.message}`; }
    toast(`Verifikasi gagal: ${err.message}`, "error");
  }
}

async function onSrcDbSelected(cardId, dbName) {
  const card = state.srcDbCards.find(c => c.id === cardId);
  if (!card) return;

  card.database = dbName;
  card.tables   = [];
  card._availableTables = [];
  state.srcColumns         = [];
  state.srcSelectedColumns = [];
  state.srcSelectedTable   = "";
  renderSrcDbCards();

  if (!dbName) return;

  try {
    const { host, port, user, password } = card._connOpts || card;
    const q = new URLSearchParams({ type: state.srcDbType, host, port, user, password, database: dbName });
    const res = await fetch(`${API.listTables}?${q}`);
    if (!res.ok) throw new Error("Gagal load tabel");
    const data = await res.json();
    card._availableTables = data.tables || [];
    renderSrcDbCards();
  } catch (e) {
    toast(`Gagal load tabel: ${e.message}`, "error");
  }
}

function addSrcDbCard() {
  const id = ++state.srcDbCardCounter;
  const card = { id, verified: false, host: "", port: "", user: "", password: "", database: "", tables: [], _databases: [], _availableTables: [], _connOpts: null };
  state.srcDbCards.push(card);
  renderSrcDbCards();
}

function removeSrcDbCard(id) {
  state.srcDbCards = state.srcDbCards.filter(c => c.id !== id);
  renderSrcDbCards();
}

function renderSrcDbCards() {
  const container = $("#src-db-cards");
  if (!container) return;
  container.innerHTML = "";
  state.srcDbCards.forEach(card => {
    const defaultPort = String(getDbDefaultPort(state.srcDbType));
    const div = document.createElement("div");
    div.className = "source-card";
    div.id = `src-card-${card.id}`;
    div.innerHTML = `
      <div class="source-card-header">
        <div class="source-card-title">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect><rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect><line x1="6" y1="6" x2="6.01" y2="6"></line><line x1="6" y1="18" x2="6.01" y2="18"></line></svg>
          Database #${card.id}
        </div>
        ${state.srcDbCards.length > 1 ? `
          <button class="source-card-remove" onclick="removeSrcDbCard(${card.id})" title="Hapus">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        ` : ""}
      </div>

      <!-- Step indicator -->
      <div class="step-indicator">
        <div class="step-dot ${card.verified ? 'done' : 'active'}">1</div>
        <div class="step-line ${card.verified ? 'done' : ''}"></div>
        <div class="step-dot ${card.database ? 'active' : ''}">2</div>
        <div class="step-line ${card.tables.length > 0 ? 'done' : ''}"></div>
        <div class="step-dot ${card.tables.length > 0 ? 'active' : ''}">3</div>
      </div>

      <!-- Step 1: Connection -->
      <div style="display:grid;grid-template-columns:1fr 80px;gap:8px;margin-bottom:8px">
        <input class="form-control" id="src-host-${card.id}" type="text" placeholder="localhost" value="${card.host}" oninput="updateSrcCardField(${card.id},'host',this.value)">
        <input class="form-control src-db-port-input" id="src-port-${card.id}" type="number" placeholder="${defaultPort}" value="${card.port}" oninput="updateSrcCardField(${card.id},'port',this.value)">
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px">
        <input class="form-control" id="src-user-${card.id}" type="text" placeholder="root" value="${card.user}" oninput="updateSrcCardField(${card.id},'user',this.value)">
        <input class="form-control" id="src-pass-${card.id}" type="password" placeholder="password" value="${card.password}" oninput="updateSrcCardField(${card.id},'password',this.value)">
      </div>
      <button class="verify-btn ${card.verified ? 'verified' : ''}" id="src-verify-btn-${card.id}" onclick="verifySrcCard(${card.id})">
        ${card.verified
          ? `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg> Terverifikasi`
          : `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg> Verifikasi Koneksi`}
      </button>
      <div id="src-verify-msg-${card.id}" style="font-size:11.5px;margin-top:5px;color:var(--text-tertiary)"></div>

      <!-- Step 2: Database dropdown (after verify) -->
      <div id="src-db-group-${card.id}" style="display:${card.verified ? '' : 'none'};margin-top:10px">
        <label class="form-label">Pilih Database</label>
        <select class="form-select" id="src-db-sel-${card.id}" onchange="onSrcDbSelected(${card.id}, this.value)">
          <option value="">— Pilih database —</option>
          ${(card._databases || []).map(db => `<option value="${db}" ${db === card.database ? 'selected' : ''}>${db}</option>`).join("")}
        </select>
      </div>

      <!-- Step 3: Table select (1 table focus) -->
      <div id="src-table-group-${card.id}" style="display:${card.database ? '' : 'none'};margin-top:10px">
        <label class="form-label">Pilih 1 Tabel Sumber</label>
        <div class="table-chips-container" id="src-table-chips-${card.id}">
          ${(card._availableTables || []).map(t => `
            <span class="table-chip-selectable ${card.tables.includes(t) ? 'selected' : ''}"
                  onclick="selectSingleSrcTable(${card.id}, '${t}')">
              <svg class="chip-check" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
              ${t}
            </span>
          `).join("")}
          ${!(card._availableTables || []).length ? '<span style="font-size:11.5px;color:var(--text-tertiary)">Pilih database terlebih dahulu</span>' : ''}
        </div>
        <div style="font-size:11px;color:var(--text-tertiary);margin-top:4px">
          ${card.tables.length > 0 ? `<span class="verified-badge"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg> Tabel <strong>${card.tables[0]}</strong> dipilih</span>` : "Pilih 1 tabel sumber untuk melihat kolom"}
        </div>

        <!-- Step 4: Column Selection Checklist -->
        ${renderSrcColumnChecklist(card)}
      </div>
    `;
    container.appendChild(div);
  });
}

function renderSrcColumnChecklist(card) {
  if (!card.tables.length || !state.srcColumns.length) return "";
  return `
    <div class="column-checklist-box">
      <div class="column-checklist-header">
        <div class="column-checklist-title">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
          Pilih Kolom Sumber (${state.srcSelectedColumns.length}/${state.srcColumns.length} dipilih)
        </div>
        <div style="display:flex;gap:6px">
          <button type="button" class="btn btn-secondary btn-sm" style="padding:2px 8px;font-size:10.5px" onclick="toggleAllSourceCols(true)">Pilih Semua</button>
          <button type="button" class="btn btn-secondary btn-sm" style="padding:2px 8px;font-size:10.5px" onclick="toggleAllSourceCols(false)">Kosongkan</button>
        </div>
      </div>
      <div class="column-checklist-grid">
        ${state.srcColumns.map(col => `
          <label class="column-check-item">
            <div style="display:flex;align-items:center">
              <input type="checkbox" value="${col.name}" ${state.srcSelectedColumns.includes(col.name) ? 'checked' : ''} onchange="toggleSourceColumn('${col.name}', this.checked)">
              <span style="font-weight:500">${col.name}</span>
            </div>
            <span class="column-type-badge">${col.type}</span>
          </label>
        `).join("")}
      </div>
      <div style="font-size:11px;color:var(--text-tertiary);margin-top:6px">
        Kolom yang dicentang akan ditransformasikan dan dikirim ke tabel target.
      </div>
    </div>
  `;
}

async function selectSingleSrcTable(cardId, tableName) {
  const card = state.srcDbCards.find(c => c.id === cardId);
  if (!card) return;

  if (card.tables.includes(tableName)) {
    card.tables = [];
    state.srcSelectedTable = "";
    state.srcColumns = [];
    state.srcSelectedColumns = [];
    state.columnMapping = {};
    renderSrcDbCards();
    renderColumnMapping();
    renderColumnTransformRules();
    return;
  }

  card.tables = [tableName];
  state.srcSelectedTable = tableName;
  state.columnMapping = {};
  toast(`Memuat kolom tabel '${tableName}'...`, "info", 2000);

  try {
    const q = `type=${state.srcDbType}&host=${card.host}&port=${card.port}&user=${card.user}&password=${encodeURIComponent(card.password)}&database=${card.database}&table=${tableName}`;
    const res = await fetch(`${API.listColumns}?${q}`);
    const data = await res.json();
    state.srcColumns = data.columns || [];
    state.srcSelectedColumns = state.srcColumns.map(c => c.name);
  } catch (e) {
    toast("Gagal memuat kolom tabel: " + e.message, "error");
  }

  renderSrcDbCards();
  renderColumnMapping();
  renderColumnTransformRules();
}

function toggleAllSourceCols(selectAll) {
  state.srcSelectedColumns = selectAll ? state.srcColumns.map(c => c.name) : [];
  renderSrcDbCards();
  renderColumnMapping();
  renderColumnTransformRules();
}

function toggleSourceColumn(colName, isChecked) {
  if (isChecked) {
    if (!state.srcSelectedColumns.includes(colName)) state.srcSelectedColumns.push(colName);
  } else {
    state.srcSelectedColumns = state.srcSelectedColumns.filter(c => c !== colName);
  }
  renderSrcDbCards();
  renderColumnMapping();
  renderColumnTransformRules();
}

// ── DESTINATION: Category switch ────────────────────────────────────────────
function setDstCategory(cat) {
  state.dstCategory = cat;
  $("#dst-cat-file")?.classList.toggle("selected", cat === "file");
  $("#dst-cat-sql")?.classList.toggle("selected", cat === "sql");
  $("#dst-panel-file").style.display = cat === "file" ? "" : "none";
  $("#dst-panel-sql").style.display  = cat === "sql"  ? "" : "none";
}

function selectDstFileFormat(fmt) {
  state.dstFileFormat = fmt;
  $$("[data-fmt]", $("#dst-file-format-group")).forEach(btn => {
    btn.classList.toggle("selected", btn.dataset.fmt === fmt);
  });
  const ext = (fmt === "excel" || fmt === "xlsx") ? ".xlsx" : `.${fmt}`;
  const extSpan = $("#dst-file-ext");
  if (extSpan) extSpan.textContent = ext;
  // Show table name field for SQLite
  const sqliteGroup = $("#dst-sqlite-table-group");
  if (sqliteGroup) sqliteGroup.style.display = fmt === "sqlite" ? "" : "none";
}

function selectDstDbType(dbtype) {
  state.dstDbType = dbtype;
  $$("[data-dbtype]", $("#dst-panel-sql")).forEach(btn => {
    btn.classList.toggle("selected", btn.dataset.dbtype === dbtype);
  });
  // Update default port placeholder
  const portInput = $("#dst-port");
  if (portInput) portInput.placeholder = String(getDbDefaultPort(dbtype));
  // Reset verification
  state.dstVerified = false;
  state.dstDatabases = [];
  const dbGroup   = $("#dst-db-select-group");
  const tblGroup  = $("#dst-table-select-group");
  if (dbGroup)  dbGroup.style.display  = "none";
  if (tblGroup) tblGroup.style.display = "none";
  const status = $("#dst-verify-status");
  if (status)  status.textContent = "";
  const btn = $("#dst-verify-btn");
  if (btn) { btn.className = "verify-btn"; btn.textContent = "Verifikasi Koneksi"; }
}

async function verifyDstConnection() {
  const host     = $("#dst-host")?.value.trim();
  const port     = parseInt($("#dst-port")?.value) || getDbDefaultPort(state.dstDbType);
  const user     = $("#dst-user")?.value.trim();
  const password = $("#dst-password")?.value || "";

  if (!host || !user) { toast("Host dan User wajib diisi.", "error"); return; }

  const btn    = $("#dst-verify-btn");
  const status = $("#dst-verify-status");
  if (btn) { btn.classList.add("loading"); btn.disabled = true; }
  if (status) status.textContent = "Menghubungkan...";

  try {
    const res  = await fetch(API.verifyConn, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type: state.dstDbType, host, port, user, password }),
    });
    const data = await res.json();

    if (data.ok) {
      state.dstVerified = true;
      if (btn) { btn.className = "verify-btn verified"; btn.innerHTML = `✓ Terverifikasi`; }
      if (status) status.innerHTML = `<span class="verified-badge">✓ Koneksi berhasil!</span>`;

      // Load databases
      const dbRes  = await fetch(`${API.listDatabases}?type=${state.dstDbType}&host=${host}&port=${port}&user=${user}&password=${encodeURIComponent(password)}`);
      const dbData = await dbRes.json();
      const dbs    = dbData.databases || [];
      state.dstDatabases = dbs;

      const sel = $("#dst-db-dropdown");
      if (sel) {
        sel.innerHTML = `<option value="">— Pilih database —</option>` +
          dbs.map(db => `<option value="${db}">${db}</option>`).join("");
        sel.onchange = () => onDstDbSelected(sel.value);
      }
      const dbGroup = $("#dst-db-select-group");
      if (dbGroup) dbGroup.style.display = "";
    } else {
      state.dstVerified = false;
      if (btn) { btn.className = "verify-btn failed"; }
      if (status) status.textContent = `✕ ${data.error || "Koneksi gagal"}`;
    }
  } catch (e) {
    state.dstVerified = false;
    if (status) status.textContent = `✕ ${e.message}`;
  } finally {
    if (btn) { btn.classList.remove("loading"); btn.disabled = false; }
  }
}

function setDstTableMode(mode) {
  state.dstTableMode = mode;
  $("#dst-mode-existing-btn")?.classList.toggle("selected", mode === "existing");
  $("#dst-mode-new-btn")?.classList.toggle("selected", mode === "new");
  const existCont = $("#dst-table-existing-container");
  const newCont   = $("#dst-table-new-container");
  if (existCont) existCont.style.display = mode === "existing" ? "" : "none";
  if (newCont)   newCont.style.display   = mode === "new" ? "" : "none";

  if (mode === "existing" && state.dstSelectedTable) {
    renderColumnMapping();
  } else {
    const mapBox = $("#dst-column-mapping-container");
    if (mapBox) mapBox.style.display = "none";
  }
}

function setDstLoadMode(mode) {
  state.dstLoadMode = mode;
}

async function onDstDbSelected(database) {
  const tableGroup = $("#dst-table-select-group");
  const mapBox = $("#dst-column-mapping-container");
  if (!database) {
    if (tableGroup) tableGroup.style.display = "none";
    if (mapBox) mapBox.style.display = "none";
    return;
  }

  const host     = $("#dst-host")?.value.trim() || "localhost";
  const port     = parseInt($("#dst-port")?.value) || getDbDefaultPort(state.dstDbType);
  const user     = $("#dst-user")?.value.trim() || "root";
  const password = $("#dst-password")?.value || "";

  try {
    const q   = `type=${state.dstDbType}&host=${host}&port=${port}&user=${user}&password=${encodeURIComponent(password)}&database=${database}`;
    const res = await fetch(`${API.listTables}?${q}`);
    const data = await res.json();
    state.dstAvailableTables = data.tables || [];

    const sel = $("#dst-table-dropdown");
    if (sel) {
      sel.innerHTML = `<option value="">— Pilih tabel tujuan yang sudah ada —</option>` +
        state.dstAvailableTables.map(t => `<option value="${t}" ${t === state.dstSelectedTable ? 'selected' : ''}>${t}</option>`).join("");
    }
    if (tableGroup) tableGroup.style.display = "";
  } catch (e) {
    toast("Gagal memuat tabel destination: " + e.message, "error");
  }
}

async function onDstTableSelected(tableName) {
  state.dstSelectedTable = tableName;
  state.columnMapping = {}; // Reset pemetaan saat tabel tujuan berubah
  const loadModeGroup = $("#dst-load-mode-group");
  if (!tableName) {
    const mapBox = $("#dst-column-mapping-container");
    if (mapBox) mapBox.style.display = "none";
    if (loadModeGroup) loadModeGroup.style.display = "none";
    return;
  }

  if (loadModeGroup) loadModeGroup.style.display = "";

  const host     = $("#dst-host")?.value.trim() || "localhost";
  const port     = parseInt($("#dst-port")?.value) || getDbDefaultPort(state.dstDbType);
  const user     = $("#dst-user")?.value.trim() || "root";
  const password = $("#dst-password")?.value || "";
  const database = $("#dst-db-dropdown")?.value;

  try {
    const q   = `type=${state.dstDbType}&host=${host}&port=${port}&user=${user}&password=${encodeURIComponent(password)}&database=${database}&table=${tableName}`;
    const res = await fetch(`${API.listColumns}?${q}`);
    const data = await res.json();
    state.dstColumns = data.columns || [];
    renderColumnMapping();
  } catch (e) {
    toast("Gagal memuat kolom tabel target: " + e.message, "error");
  }
}

function autoMatchColumns() {
  state.columnMapping = {};
  const matchedTargets = new Set();
  state.srcSelectedColumns.forEach(srcName => {
    const srcClean = srcName.toLowerCase().replace(/[^a-z0-9]/g, "");
    let match = state.dstColumns.find(d => 
      d.name.toLowerCase() === srcName.toLowerCase() && !matchedTargets.has(d.name.toLowerCase())
    );
    if (!match) {
      match = state.dstColumns.find(d => 
        d.name.toLowerCase().replace(/[^a-z0-9]/g, "") === srcClean && !matchedTargets.has(d.name.toLowerCase())
      );
    }
    if (match) {
      state.columnMapping[srcName] = match.name;
      matchedTargets.add(match.name.toLowerCase());
    } else {
      state.columnMapping[srcName] = "__ignore__";
    }
  });
  renderColumnMapping();
  toast("Pemetaan otomatis berdasarkan kecocokan nama kolom selesai.", "info", 2000);
}

function positionalMatchColumns() {
  state.columnMapping = {};
  state.srcSelectedColumns.forEach((srcName, idx) => {
    if (idx < state.dstColumns.length) {
      state.columnMapping[srcName] = state.dstColumns[idx].name;
    } else {
      state.columnMapping[srcName] = "__ignore__";
    }
  });
  renderColumnMapping();
  toast("Pemetaan 1-ke-1 berurutan diterapkan (tanpa duplikasi).", "info", 2000);
}

function ignoreAllColumns() {
  state.srcSelectedColumns.forEach(srcName => {
    state.columnMapping[srcName] = "__ignore__";
  });
  renderColumnMapping();
  toast("Semua pemetaan diubah ke Abaikan.", "info", 1500);
}

function renderColumnMapping() {
  const container = $("#dst-column-mapping-container");
  if (!container) return;

  if (state.dstTableMode !== "existing" || !state.dstSelectedTable || !state.srcSelectedColumns.length || !state.dstColumns.length) {
    container.style.display = "none";
    return;
  }

  // Preserve scroll position
  const scrollPos = container.querySelector(".column-mapping-table")?.scrollTop || 0;

  // Auto-match unmapped columns without duplicate targets
  const matchedTargets = new Set(
    Object.values(state.columnMapping).filter(v => v && v !== "__ignore__").map(v => v.toLowerCase())
  );

  state.srcSelectedColumns.forEach(srcName => {
    if (!state.columnMapping[srcName]) {
      const srcClean = srcName.toLowerCase().replace(/[^a-z0-9]/g, "");
      let match = state.dstColumns.find(d => 
        d.name.toLowerCase() === srcName.toLowerCase() && !matchedTargets.has(d.name.toLowerCase())
      );
      if (!match) {
        match = state.dstColumns.find(d => 
          d.name.toLowerCase().replace(/[^a-z0-9]/g, "") === srcClean && !matchedTargets.has(d.name.toLowerCase())
        );
      }
      if (match) {
        state.columnMapping[srcName] = match.name;
        matchedTargets.add(match.name.toLowerCase());
      } else {
        state.columnMapping[srcName] = "__ignore__";
      }
    }
  });

  // Calculate duplicate targets
  const targetCounts = {};
  for (const srcName of state.srcSelectedColumns) {
    const dst = state.columnMapping[srcName];
    if (dst && dst !== "__ignore__") {
      const k = dst.toLowerCase();
      targetCounts[k] = (targetCounts[k] || 0) + 1;
    }
  }

  const hasDuplicate = Object.values(targetCounts).some(cnt => cnt > 1);

  container.style.display = "";
  container.innerHTML = `
    <div class="column-mapping-box">
      <div class="column-mapping-header">
        <div>
          <h4>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 3h5v5M4 20L21 3M21 16v5h-5M15 15l6 6M4 4l5 5"/></svg>
            Pemetaan Kolom (Sumber ──► Tabel Target: ${state.dstSelectedTable})
          </h4>
          <span style="font-size:11px;color:var(--text-tertiary)">Pilih kolom target yang diisi untuk setiap kolom sumber</span>
        </div>
        <div class="mapping-quick-actions">
          <button type="button" class="mapping-btn-small" onclick="autoMatchColumns()" title="Cocokkan berdasarkan nama kolom yang mirip">Cocokkan Nama</button>
          <button type="button" class="mapping-btn-small" onclick="positionalMatchColumns()" title="Petakan berurutan kolom ke-1 ke kolom ke-1, dll tanpa duplikat">1-ke-1 Berurutan</button>
          <button type="button" class="mapping-btn-small" onclick="ignoreAllColumns()" title="Set semua ke Abaikan">Abaikan Semua</button>
        </div>
      </div>

      ${hasDuplicate ? `
        <div style="background:var(--red-tint);color:var(--red-text);border:1px solid rgba(255,59,48,0.25);padding:7px 10px;border-radius:6px;font-size:11.5px;font-weight:600;margin-bottom:8px;display:flex;align-items:center;gap:6px">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          Ada kolom tujuan yang dipilih lebih dari sekali. Setiap kolom tujuan hanya boleh menerima 1 kolom sumber.
        </div>
      ` : ''}

      <div class="column-mapping-table">
        ${state.srcSelectedColumns.map(srcName => {
          const srcCol = state.srcColumns.find(c => c.name === srcName);
          const srcType = srcCol ? srcCol.type : "";
          const currentDst = state.columnMapping[srcName] || "__ignore__";
          const isDup = currentDst !== "__ignore__" && targetCounts[currentDst.toLowerCase()] > 1;

          return `
            <div class="column-mapping-row" style="${isDup ? 'background:rgba(255,59,48,0.06);border:1px solid rgba(255,59,48,0.3)' : ''}">
              <div class="mapping-src-col" title="${srcName}">
                <span>${srcName}</span>
                ${srcType ? `<span class="column-type-badge">${srcType}</span>` : ""}
              </div>
              <span class="mapping-arrow">──►</span>
              <select class="form-select mapping-dst-select ${isDup ? 'duplicate' : ''}" onchange="updateColumnMapping('${srcName}', this.value)">
                <option value="__ignore__" ${currentDst === '__ignore__' ? 'selected' : ''}>— Abaikan / Jangan Isi —</option>
                ${state.dstColumns.map(dc => `
                  <option value="${dc.name}" ${currentDst === dc.name ? 'selected' : ''}>
                    ${dc.name} (${dc.type})
                  </option>
                `).join("")}
              </select>
              ${isDup ? `<div class="mapping-dup-warning"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg> Kolom '${currentDst}' dipilih juga oleh kolom sumber lain. Ubah salah satunya.</div>` : ''}
            </div>
          `;
        }).join("")}
      </div>
      <div style="font-size:11px;color:var(--text-tertiary);margin-top:8px">
        ✓ Data hasil transformasi akan otomatis mengisi kolom-kolom tabel target yang Anda pilih di atas. Kolom yang diatur ke "— Abaikan —" tidak akan dimasukkan.
      </div>
    </div>
  `;

  const newTable = container.querySelector(".column-mapping-table");
  if (newTable && scrollPos > 0) newTable.scrollTop = scrollPos;
}

function updateColumnMapping(srcCol, dstCol) {
  state.columnMapping[srcCol] = dstCol;
  renderColumnMapping();
}

function resetTaskBuilder() {
  state.taskCounter = (state.taskCounter || 1) + 1;
  state.pipelineName = `Task ${state.taskCounter}: Sinkronisasi Data`;
  const nameInput = $("#pipeline-name-input");
  if (nameInput) nameInput.value = state.pipelineName;

  // 1. Reset Sumber Data (Tabel & Kolom)
  state.srcColumns = [];
  state.srcSelectedColumns = [];
  state.srcSelectedTable = "";
  if (state.srcDbCards && state.srcDbCards.length > 0) {
    state.srcDbCards.forEach(c => { c.tables = []; });
  }

  // 2. Reset Tabel Tujuan
  state.dstSelectedTable = "";
  state.dstColumns = [];
  const dstTableSelect = $("#dst-table-dropdown");
  if (dstTableSelect) dstTableSelect.value = "";
  const dstTableNameInput = $("#dst-table-name");
  if (dstTableNameInput) dstTableNameInput.value = "";

  // 3. Reset Mode Load ke sync
  state.dstLoadMode = "sync";
  const radioSync = $("#dst-mode-sync");
  if (radioSync) radioSync.checked = true;
  const loadModeGroup = $("#dst-load-mode-group");
  if (loadModeGroup) loadModeGroup.style.display = "none";

  // 4. Reset Pemetaan Kolom
  state.columnMapping = {};
  const mapCont = $("#dst-column-mapping-container");
  if (mapCont) { mapCont.style.display = "none"; mapCont.innerHTML = ""; }

  // 5. Reset Transformasi per Kolom & Global
  state.columnTransformRules = [];
  state.ruleCounter = 0;
  ["trim", "capitalize", "uppercase", "lowercase", "fill-null", "mask"].forEach(t => {
    const cb = $(`#transform-${t}`);
    if (cb) cb.checked = false;
  });
  updateTransformBadge();
  renderColumnTransformRules();

  // 6. Render ulang kartu sumber data
  renderSrcDbCards();
  toast(`Task baru siap: ${state.pipelineName}`, "success");
}

// ── Drag & Drop for upload zone ─────────────────────────────────────────────
function initDropZone() {
  const zone = $("#src-drop-zone");
  if (!zone) return;
  zone.addEventListener("dragover", e => { e.preventDefault(); zone.classList.add("dragover"); });
  zone.addEventListener("dragleave", () => zone.classList.remove("dragover"));
  zone.addEventListener("drop", e => {
    e.preventDefault();
    zone.classList.remove("dragover");
    const files = e.dataTransfer?.files;
    if (files && files.length) handleSrcFileSelect(files);
  });
}

// ── Collect sources for pipeline run ────────────────────────────────────────
function collectSources() {
  if (state.srcCategory === "file") {
    if (state.srcUploadedFiles.length === 0) return null;
    // Build column_types map from current srcColumns (user may have overridden types)
    const columnTypes = {};
    for (const col of (state.srcColumns || [])) {
      if (col.name && col.type) columnTypes[col.name] = col.type;
    }
    return state.srcUploadedFiles.map(f => {
      const opts = { path: f.path };
      if (state.srcFileFormat === "csv" && $("#src-csv-delimiter")?.value) {
        opts.delimiter = $("#src-csv-delimiter").value;
      }
      if (state.srcFileFormat === "sqlite") {
        const tbl = $("#src-sqlite-table")?.value.trim();
        if (tbl) opts.table_name = tbl;
      }
      // Attach column type overrides so backend can cast before loading into SQL
      if (Object.keys(columnTypes).length > 0) {
        opts.column_types = columnTypes;
      }
      return { type: state.srcFileFormat, options: opts };
    });
  } else {
    // Single DB & Single Table focus
    const card = state.srcDbCards.find(c => c.verified && c.database && c.tables.length > 0);
    if (!card) return null;
    return [{
      type: state.srcDbType,
      options: {
        host: card.host,
        port: parseInt(card.port) || getDbDefaultPort(state.srcDbType),
        user: card.user,
        password: card.password,
        database: card.database,
        table_name: card.tables[0],
      },
    }];
  }
}

function collectDestination() {
  if (state.dstCategory === "file") {
    const name = $("#dst-file-name")?.value.trim() || "output";
    const fmt  = state.dstFileFormat;
    const ext  = (fmt === "excel" || fmt === "xlsx") ? "xlsx" : fmt;
    const path = `output/${name}.${ext}`;
    const opts = { path };
    if (fmt === "sqlite") {
      opts.table_name = $("#dst-sqlite-table")?.value.trim() || "etl_output";
    }
    return { type: fmt, options: opts };
  } else {
    if (!state.dstVerified) return null;
    const database = $("#dst-db-dropdown")?.value;
    const tableName = state.dstTableMode === "existing"
      ? state.dstSelectedTable
      : $("#dst-table-name")?.value.trim();
    if (!database || !tableName) return null;
    return {
      type: state.dstDbType,
      options: {
        host: $("#dst-host")?.value.trim() || "localhost",
        port: parseInt($("#dst-port")?.value) || getDbDefaultPort(state.dstDbType),
        user: $("#dst-user")?.value.trim() || "root",
        password: $("#dst-password")?.value || "",
        database,
        table_name: tableName,
        if_exists: state.dstLoadMode || "append",
      },
    };
  }
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
    _cachedHistoryRuns = runs || [];
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
      <td style="display:flex;gap:6px;align-items:center;flex-wrap:nowrap">
        <button class="btn btn-secondary btn-sm" onclick="loadHistoryToBuilder('${r.run_id}')"
                title="Buka & edit kembali konfigurasi task ini di Pipeline Builder"
                style="padding:4px 9px;font-size:11.5px;display:inline-flex;align-items:center;gap:4px">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 20h9"></path>
            <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
          </svg>
          Edit di Builder
        </button>
        <button class="btn btn-secondary btn-sm" onclick="scheduleFromHistory('${r.run_id}')"
                title="Jadwalkan task ini secara otomatis"
                style="padding:4px 9px;font-size:11.5px;display:inline-flex;align-items:center;gap:4px">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="16" y1="2" x2="16" y2="6"></line>
            <line x1="8" y1="2" x2="8" y2="6"></line>
            <line x1="3" y1="10" x2="21" y2="10"></line>
          </svg>
          Jadwalkan
        </button>
        ${r.output_file ? `
          <a href="${API.download(r.output_file)}" download class="btn btn-secondary btn-sm"
             style="padding:4px 9px;font-size:11.5px;text-decoration:none;display:inline-flex;align-items:center;gap:4px">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
            Unduh
          </a>` : ''}
      </td>
    </tr>
  `).join("");
}

function scheduleFromHistory(runId) {
  showCreateScheduleModal();
  setTimeout(() => {
    const sel = $("#sc-history-picker");
    if (sel) {
      sel.value = runId;
      onSelectHistoryForSchedule(runId);
    }
  }, 100);
}

async function loadHistoryToBuilder(runId) {
  let run = (_cachedHistoryRuns || []).find(r => r.run_id === runId);
  if (!run) {
    try {
      const res = await fetch(API.history);
      const runs = await res.json();
      _cachedHistoryRuns = runs || [];
      run = runs.find(r => r.run_id === runId);
    } catch (_) {}
  }
  if (!run) {
    toast("Data riwayat tidak ditemukan.", "error");
    return;
  }

  // 1. Pindah ke view builder
  showView("builder");

  // 2. Set nama pipeline
  state.pipelineName = run.pipeline_name || "Edited Pipeline";
  const nameInput = $("#pipeline-name-input");
  if (nameInput) nameInput.value = state.pipelineName;

  // 3. Reset state kolom & mapping lama
  state.srcColumns = [];
  state.srcSelectedColumns = [];
  state.srcSelectedTable = "";
  state.dstSelectedTable = "";
  state.dstColumns = [];
  state.columnMapping = {};

  // 4. Source setup
  const rawSrcType = run.source_type || "csv";
  const cleanSrcType = rawSrcType.split("+")[0];
  const isSrcSql = ["mysql", "postgresql", "postgres", "oracle"].includes(cleanSrcType);
  const srcOpts = run.source_options || (run.sources && run.sources[0]?.options) || {};

  if (isSrcSql) {
    setSrcCategory("sql");
    selectSrcDbType(cleanSrcType === "postgres" ? "postgresql" : cleanSrcType);

    if (state.srcDbCards.length === 0) addSrcDbCard();
    const card = state.srcDbCards[0];
    card.host = srcOpts.host || "localhost";
    card.port = srcOpts.port || getDbDefaultPort(cleanSrcType);
    card.user = srcOpts.user || "root";
    card.password = srcOpts.password || "";
    card.database = srcOpts.database || "";
    const srcTable = srcOpts.table_name || srcOpts.table || "";
    card.tables = srcTable ? [srcTable] : [];
    card._connOpts = { host: card.host, port: card.port, user: card.user, password: card.password };
    card.verified = true;

    // Load available databases & tables
    try {
      const params = new URLSearchParams({ type: state.srcDbType, host: card.host, port: card.port, user: card.user, password: card.password });
      const dbRes = await fetch(`${API.listDatabases}?${params}`);
      if (dbRes.ok) {
        const dbData = await dbRes.json();
        card._databases = dbData.databases || [];
      }
      if (card.database) {
        const q = new URLSearchParams({ type: state.srcDbType, host: card.host, port: card.port, user: card.user, password: card.password, database: card.database });
        const tRes = await fetch(`${API.listTables}?${q}`);
        if (tRes.ok) {
          const tData = await tRes.json();
          card._availableTables = tData.tables || [];
        }
      }
    } catch (_) {}

    renderSrcDbCards();
    if (card.database && srcTable) {
      await selectSingleSrcTable(card.id, srcTable);
    }
  } else {
    setSrcCategory("file");
    selectSrcFileFormat(cleanSrcType);
    if (srcOpts.path) {
      state.srcUploadedFiles = [{
        original_name: srcOpts.path.split("/").pop(),
        path: srcOpts.path,
        size_formatted: "Tersimpan",
      }];
      renderUploadedFiles();
    }
  }

  // 5. Destination setup
  const dstType = run.destination_type || "csv";
  const isDstSql = ["mysql", "postgresql", "postgres", "oracle"].includes(dstType);
  const dstOpts = run.destination_options || {};

  if (isDstSql) {
    setDstCategory("sql");
    selectDstDbType(dstType === "postgres" ? "postgresql" : dstType);

    if ($("#dst-host")) $("#dst-host").value = dstOpts.host || "localhost";
    if ($("#dst-port")) $("#dst-port").value = dstOpts.port || getDbDefaultPort(dstType);
    if ($("#dst-user")) $("#dst-user").value = dstOpts.user || "root";
    if ($("#dst-password")) $("#dst-password").value = dstOpts.password || "";

    state.dstVerified = true;
    const btn = $("#dst-verify-btn");
    if (btn) { btn.className = "verify-btn verified"; btn.innerHTML = "✓ Terverifikasi"; }
    const status = $("#dst-verify-status");
    if (status) status.innerHTML = `<span class="verified-badge">✓ Koneksi berhasil!</span>`;

    try {
      const dbRes = await fetch(`${API.listDatabases}?type=${state.dstDbType}&host=${dstOpts.host || 'localhost'}&port=${dstOpts.port || getDbDefaultPort(state.dstDbType)}&user=${dstOpts.user || 'root'}&password=${encodeURIComponent(dstOpts.password || '')}`);
      if (dbRes.ok) {
        const dbData = await dbRes.json();
        state.dstDatabases = dbData.databases || [];
        const sel = $("#dst-db-dropdown");
        if (sel) {
          sel.innerHTML = `<option value="">— Pilih database —</option>` +
            state.dstDatabases.map(db => `<option value="${db}" ${db === dstOpts.database ? 'selected' : ''}>${db}</option>`).join("");
          sel.value = dstOpts.database || "";
          sel.onchange = () => onDstDbSelected(sel.value);
        }
        const dbGroup = $("#dst-db-select-group");
        if (dbGroup) dbGroup.style.display = "";
      }

      if (dstOpts.database) {
        await onDstDbSelected(dstOpts.database);
        const dstTable = dstOpts.table_name || dstOpts.table || "";
        if (dstTable) {
          state.dstSelectedTable = dstTable;
          const tSel = $("#dst-table-dropdown");
          if (tSel) tSel.value = dstTable;
          await onDstTableSelected(dstTable);
        }
      }
    } catch (_) {}

    if (dstOpts.load_mode) {
      setDstLoadMode(dstOpts.load_mode);
      const radio = $(`#dst-mode-${dstOpts.load_mode}`);
      if (radio) radio.checked = true;
    }

    if (dstOpts.column_mapping) {
      state.columnMapping = { ...dstOpts.column_mapping };
      renderColumnMapping();
    }
  } else {
    setDstCategory("file");
    selectDstFileFormat(dstType);
    if (dstOpts.path) {
      const fName = dstOpts.path.split("/").pop().replace(/\.[^/.]+$/, "");
      if ($("#dst-file-name")) $("#dst-file-name").value = fName;
    }
  }

  // 6. Transformations setup
  state.columnTransformRules = [];
  state.ruleCounter = 0;
  if (Array.isArray(run.transformations)) {
    run.transformations.forEach(t => {
      const cols = t.params?.columns || (t.column ? [t.column] : []);
      if (cols.length) {
        cols.forEach(c => {
          state.columnTransformRules.push({
            id: ++state.ruleCounter,
            column: c,
            type: t.type,
            params: { ...t.params },
          });
        });
      } else {
        const cb = $(`#transform-${t.type}`);
        if (cb) cb.checked = true;
      }
    });
  }
  renderColumnTransformRules();
  updateTransformBadge();

  // 7. Feedback toast & scroll
  window.scrollTo({ top: 0, behavior: "smooth" });
  toast(`Konfigurasi "${run.pipeline_name}" berhasil dimuat ke Pipeline Builder!`, "success");
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

// ─── Theme Management (Apple HIG Light / Dark) ──────────────────────────────

function initTheme() {
  const urlParams = new URLSearchParams(window.location.search);
  const themeParam = urlParams.get("theme");
  const saved = (themeParam === "dark" || themeParam === "light") ? themeParam : localStorage.getItem("flowetl_theme");
  const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  const initial = saved || (prefersDark ? "dark" : "light");
  setTheme(initial, !themeParam);

  if (window.matchMedia) {
    try {
      window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (e) => {
        if (!localStorage.getItem("flowetl_theme")) {
          setTheme(e.matches ? "dark" : "light", false);
        }
      });
    } catch (_) {}
  }
}

function setTheme(theme, save = true) {
  document.documentElement.setAttribute("data-theme", theme);
  if (save) {
    try { localStorage.setItem("flowetl_theme", theme); } catch (_) {}
  }
  const btn = document.getElementById("theme-toggle-btn");
  if (btn) {
    if (theme === "dark") {
      // Sun icon to switch to light
      btn.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="5"></circle>
        <line x1="12" y1="1" x2="12" y2="3"></line>
        <line x1="12" y1="21" x2="12" y2="23"></line>
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
        <line x1="1" y1="12" x2="3" y2="12"></line>
        <line x1="21" y1="12" x2="23" y2="12"></line>
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
      </svg>`;
      btn.title = "Beralih ke Mode Terang (Light Mode)";
      btn.setAttribute("aria-label", "Switch to light mode");
    } else {
      // Moon icon to switch to dark
      btn.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
      </svg>`;
      btn.title = "Beralih ke Mode Gelap (Dark Mode)";
      btn.setAttribute("aria-label", "Switch to dark mode");
    }
  }
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "light";
  const next = current === "dark" ? "light" : "dark";
  setTheme(next, true);
}

// ─── Init ─────────────────────────────────────────────────────────────────────

async function init() {
  initTheme();
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

  // Initial view from URL parameter or hash (#builder, ?view=builder)
  const urlParams = new URLSearchParams(window.location.search);
  const viewParam = urlParams.get("view") || window.location.hash.replace("#", "");
  const validViews = ["dashboard", "builder", "history", "files", "schedules"];
  const initialView = validViews.includes(viewParam) ? viewParam : "dashboard";
  showView(initialView);
  updateDashboardStats();

  window.addEventListener("hashchange", () => {
    const h = window.location.hash.replace("#", "");
    if (validViews.includes(h)) showView(h);
  });

  // Deep-link triggers for modal / drawer
  if (urlParams.get("modal") === "schedule") {
    setTimeout(() => showCreateScheduleModal(), 250);
  } else if (urlParams.get("drawer") === "progress") {
    setTimeout(() => {
      openProgressDrawer("Sinkronisasi Data Real-time (MySQL → PostgreSQL)");
      setProgress(85, "LOADING (85%)");
      const log = document.getElementById("log-console");
      if (log) {
        log.innerHTML = `
          <div style="color:var(--success)">[ 10%] CONNECTING_SOURCE ✓ Terhubung ke database sumber (MySQL)</div>
          <div style="color:var(--success)">[ 20%] CONNECTING_DESTINATION ✓ Terhubung ke target (PostgreSQL)</div>
          <div style="color:var(--accent)">[ 30%] EXTRACTING (500 baris diekstraksi)</div>
          <div style="color:var(--purple,#AF52DE)">[ 60%] TRANSFORMING (Data Cleansing: Trim, Fill Null, Capitalize)</div>
          <div style="color:var(--accent)">[ 85%] LOADING (Menyimpan 500 baris ke tabel target)</div>
        `;
      }
    }, 250);
  }
}

try { initTheme(); } catch (_) {}
document.addEventListener("DOMContentLoaded", init);
