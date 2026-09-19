import "./style.css";
import { TabManager } from "./editor/tabs";
import { defangText, refangText } from "./core/defang";
import { extractIocs, groupIocs, IOC_LABELS, type IocMatch } from "./core/iocPatterns";
import { base64Decode, base64Encode, generateHash, identifyHashTypes } from "./core/hashes";
import { downloadTextFile, exportIocsCsv, exportIocsJson, exportIocsText } from "./core/exportIocs";
import {
  hasFileSystemAccess,
  openFromDataTransferItem,
  openFromInputFile,
  pickAndOpenFile,
  pickAndSaveFile,
  writeToHandle,
} from "./core/fileSystem";
import {
  DEFAULT_SETTINGS,
  fillPlaceholders,
  loadSession,
  loadSettings,
  loadSnippets,
  loadTemplates,
  saveSession,
  saveSettings,
  saveSnippets,
  saveTemplates,
  type Settings,
} from "./core/storage";
import { initPhase3, type Phase3Hooks } from "./ui/phase3";

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
let settings: Settings = loadSettings();
let templates = loadTemplates();
let snippets = loadSnippets();
let lastIocMatches: IocMatch[] = [];
let phase3Hooks: Phase3Hooks;

document.documentElement.setAttribute("data-theme", settings.darkMode ? "dark" : "light");

// ---------------------------------------------------------------------------
// Shell
// ---------------------------------------------------------------------------
const app = document.querySelector<HTMLDivElement>("#app")!;
app.innerHTML = `
  <div class="toolbar">
    <div class="toolbar-left">
      <span class="app-title">ThreatPad</span>

      <div class="menu">
        <button class="menu-trigger">File ▾</button>
        <div class="menu-list">
          <button id="btn-new">New Tab</button>
          <button id="btn-open">Open…</button>
          <button id="btn-save">Save</button>
          <button id="btn-save-as">Save As…</button>
        </div>
      </div>

      <div class="menu">
        <button class="menu-trigger">IOC Tools ▾</button>
        <div class="menu-list">
          <button id="btn-extract" title="Ctrl+I">Extract IOCs</button>
        </div>
      </div>

      <div class="menu">
        <button class="menu-trigger">Hash ▾</button>
        <div class="menu-list">
          <button id="btn-md5">MD5</button>
          <button id="btn-sha1">SHA1</button>
          <button id="btn-sha256">SHA256</button>
          <button id="btn-identify">Identify Hash</button>
        </div>
      </div>

      <div class="menu">
        <button class="menu-trigger">Encode ▾</button>
        <div class="menu-list">
          <button id="btn-b64enc">Base64 Encode</button>
          <button id="btn-b64dec">Base64 Decode</button>
        </div>
      </div>
    </div>

    <div class="toolbar-center">
      <button id="btn-defang" class="center-action center-action-solid" title="Ctrl+D">🛡 Defang</button>
      <button id="btn-refang" class="center-action center-action-outline" title="Ctrl+R">♻ Refang</button>
    </div>

    <div class="toolbar-right">
      <select id="client-select" title="Active client"></select>

      <div class="menu menu-align-right">
        <button class="menu-trigger">Client ▾</button>
        <div class="menu-list">
          <button id="btn-manage-clients">Manage Clients…</button>
          <button id="btn-contamination-check">⚠ Contamination Check</button>
        </div>
      </div>

      <div class="menu menu-align-right">
        <button class="menu-trigger">SOC ▾</button>
        <div class="menu-list">
          <button id="btn-training-wheels">🎓 Checklist</button>
          <button id="btn-breakglass">🚨 Mistake?</button>
          <button id="btn-mileage">📊 Mileage</button>
        </div>
      </div>

      <button id="btn-theme"></button>
      <button id="btn-settings" title="Settings">⚙</button>
    </div>
  </div>
  <div class="tab-bar" id="tab-bar"></div>
  <div class="tw-panel hidden" id="tw-panel"></div>
  <div class="main">
    <div class="editor-container" id="editor"></div>
    <div class="sidebar">
      <div class="sidebar-tabs">
        <button data-panel="iocs" class="active">IOCs</button>
        <button data-panel="templates">Templates</button>
        <button data-panel="snippets">Snippets</button>
      </div>
      <div class="sidebar-panel active" id="panel-iocs"></div>
      <div class="sidebar-panel" id="panel-templates"></div>
      <div class="sidebar-panel" id="panel-snippets"></div>
    </div>
  </div>
  <div class="status-bar">
    <span id="status-left">Ready</span>
    <span class="status-right-group">
      <span id="traffic-light" class="traffic-dot" title="Content safety indicator"></span>
      <span id="timer-display">⏱ --:--</span>
      <span id="status-right"></span>
    </span>
  </div>
  <button id="btn-safe-copy" class="fab" title="Blocks copy on cross-client contamination">🔒 Safe Copy</button>
  <input type="file" id="file-input" accept=".txt,.log,.md,.csv,.json" style="display:none" />
`;

const editorContainer = document.querySelector<HTMLDivElement>("#editor")!;
const tabBar = document.querySelector<HTMLDivElement>("#tab-bar")!;
const statusLeft = document.querySelector<HTMLSpanElement>("#status-left")!;
const statusRight = document.querySelector<HTMLSpanElement>("#status-right")!;
const themeBtn = document.querySelector<HTMLButtonElement>("#btn-theme")!;
const fileInput = document.querySelector<HTMLInputElement>("#file-input")!;

// ---------------------------------------------------------------------------
// Toolbar dropdown menus
// ---------------------------------------------------------------------------
function closeAllMenus() {
  document.querySelectorAll(".menu.open").forEach((m) => m.classList.remove("open"));
}
document.querySelectorAll<HTMLDivElement>(".toolbar .menu").forEach((menu) => {
  const trigger = menu.querySelector<HTMLButtonElement>(".menu-trigger")!;
  trigger.addEventListener("click", (e) => {
    e.stopPropagation();
    const wasOpen = menu.classList.contains("open");
    closeAllMenus();
    if (!wasOpen) menu.classList.add("open");
  });
});
document.addEventListener("click", closeAllMenus);
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeAllMenus();
});

// ---------------------------------------------------------------------------
// Editor / tabs
// ---------------------------------------------------------------------------
const tabs = new TabManager(editorContainer, settings, {
  onChange: () => {
    scheduleAutosave();
    updateStatus();
    phase3Hooks?.onTextChanged();
  },
  onTabsUpdated: () => {
    renderTabBar();
    persistSession();
  },
});

const session = loadSession();
if (session && session.tabs.length > 0) {
  tabs.restore(session.tabs, session.activeTabId);
} else {
  tabs.createTab("Untitled", "");
}

function renderTabBar() {
  const activeId = tabs.activeTabId();
  tabBar.innerHTML = "";
  for (const t of tabs.list()) {
    const el = document.createElement("div");
    el.className = "tab" + (t.id === activeId ? " active" : "");
    el.innerHTML = `<span class="tab-title">${escapeHtml(t.title)}</span><span class="tab-close" data-id="${t.id}">✕</span>`;
    el.addEventListener("click", (e) => {
      if ((e.target as HTMLElement).classList.contains("tab-close")) return;
      tabs.switchTab(t.id);
      updateStatus();
    });
    el.querySelector(".tab-close")!.addEventListener("click", (e) => {
      e.stopPropagation();
      tabs.closeTab(t.id);
      phase3Hooks?.onTabClosed(t.id);
    });
    el.addEventListener("dblclick", () => {
      const name = prompt("Rename tab", t.title);
      if (name) tabs.renameTab(t.id, name);
    });
    tabBar.appendChild(el);
  }
  const newBtn = document.createElement("div");
  newBtn.className = "tab-new";
  newBtn.textContent = "+";
  newBtn.title = "New tab (Ctrl+N)";
  newBtn.addEventListener("click", () => tabs.createTab("Untitled", ""));
  tabBar.appendChild(newBtn);
}

let autosaveHandle: number | undefined;
function scheduleAutosave() {
  window.clearTimeout(autosaveHandle);
  autosaveHandle = window.setTimeout(persistSession, 400);
}
function persistSession() {
  saveSession({ tabs: tabs.serialize(), activeTabId: tabs.activeTabId() });
  const now = new Date();
  statusRight.textContent = `Saved ${now.toLocaleTimeString()}`;
}

function updateStatus() {
  const content = tabs.getContent();
  const words = content.trim() ? content.trim().split(/\s+/).length : 0;
  statusLeft.textContent = `${content.length} chars · ${words} words`;
}

function escapeHtml(s: string): string {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

// ---------------------------------------------------------------------------
// Toolbar actions
// ---------------------------------------------------------------------------
document.querySelector("#btn-new")!.addEventListener("click", () => tabs.createTab("Untitled", ""));

document.querySelector("#btn-open")!.addEventListener("click", async () => {
  if (hasFileSystemAccess) {
    try {
      const opened = await pickAndOpenFile();
      if (!opened) return; // user cancelled
      const id = tabs.createTab(opened.name, opened.content);
      if (opened.handle) tabs.attachFileHandle(id, opened.handle);
      flashStatus(`Opened ${opened.name}`);
    } catch (e) {
      alert((e as Error).message ?? "Could not open file");
    }
    return;
  }
  fileInput.click();
});
fileInput.addEventListener("change", async () => {
  const file = fileInput.files?.[0];
  fileInput.value = "";
  if (!file) return;
  try {
    const opened = await openFromInputFile(file);
    tabs.createTab(opened.name, opened.content);
    flashStatus(`Opened ${opened.name}`);
  } catch (e) {
    alert((e as Error).message ?? "Could not open file");
  }
});

async function saveActiveTab(forcePicker: boolean) {
  const activeId = tabs.activeTabId();
  const active = tabs.list().find((t) => t.id === activeId);
  const content = tabs.getContent();
  const existingHandle = activeId ? tabs.getFileHandle(activeId) : undefined;

  if (!forcePicker && existingHandle) {
    try {
      await writeToHandle(existingHandle, content);
      flashStatus(`Saved ${active?.title ?? ""}`);
      return;
    } catch (e) {
      alert(`Could not save file: ${(e as Error).message}`);
      return;
    }
  }

  if (hasFileSystemAccess) {
    try {
      const suggested = active ? active.title : "note.txt";
      const handle = await pickAndSaveFile(suggested, content);
      if (!handle) return; // user cancelled
      if (activeId) {
        tabs.attachFileHandle(activeId, handle);
        tabs.renameTab(activeId, handle.name);
      }
      flashStatus(`Saved ${handle.name}`);
    } catch (e) {
      alert(`Could not save file: ${(e as Error).message}`);
    }
    return;
  }

  const filename = active ? `${active.title}.txt` : "note.txt";
  downloadTextFile(filename, content);
  flashStatus("Saved to downloads");
}

document.querySelector("#btn-save")!.addEventListener("click", () => saveActiveTab(false));
document.querySelector("#btn-save-as")!.addEventListener("click", () => saveActiveTab(true));

// Drag & drop files onto the editor open them as new tabs.
editorContainer.addEventListener("dragover", (e) => {
  e.preventDefault();
  if (e.dataTransfer) e.dataTransfer.dropEffect = "copy";
  editorContainer.classList.add("drag-over");
});
editorContainer.addEventListener("dragleave", () => editorContainer.classList.remove("drag-over"));
editorContainer.addEventListener("drop", async (e) => {
  e.preventDefault();
  editorContainer.classList.remove("drag-over");
  const items = e.dataTransfer?.items;
  const files = e.dataTransfer?.files;
  try {
    if (items && items.length > 0) {
      for (const item of Array.from(items)) {
        if (item.kind !== "file") continue;
        const opened = await openFromDataTransferItem(item);
        if (!opened) continue;
        const id = tabs.createTab(opened.name, opened.content);
        if (opened.handle) tabs.attachFileHandle(id, opened.handle);
      }
    } else if (files) {
      for (const file of Array.from(files)) {
        const opened = await openFromInputFile(file);
        tabs.createTab(opened.name, opened.content);
      }
    }
    flashStatus("Opened dropped file(s)");
  } catch (e) {
    alert((e as Error).message ?? "Could not open dropped file");
  }
});

document.querySelector("#btn-defang")!.addEventListener("click", doDefang);
document.querySelector("#btn-refang")!.addEventListener("click", doRefang);
document.querySelector("#btn-extract")!.addEventListener("click", doExtract);

function doDefang() {
  tabs.setContent(defangText(tabs.getContent()));
  flashStatus("Defanged IOCs");
  phase3Hooks?.onDefang();
}
function doRefang() {
  tabs.setContent(refangText(tabs.getContent()));
  flashStatus("Refanged IOCs");
}
function doExtract() {
  lastIocMatches = extractIocs(tabs.getContent());
  renderIocPanel();
  switchSidebar("iocs");
  flashStatus(`Extracted ${lastIocMatches.length} IOC(s)`);
  phase3Hooks?.onExtractIocs(lastIocMatches.length);
}

document.querySelector("#btn-md5")!.addEventListener("click", () => showHash("md5"));
document.querySelector("#btn-sha1")!.addEventListener("click", () => showHash("sha1"));
document.querySelector("#btn-sha256")!.addEventListener("click", () => showHash("sha256"));

function showHash(algo: "md5" | "sha1" | "sha256") {
  const text = tabs.getSelectionOrAll();
  if (!text.trim()) return flashStatus("No text to hash");
  const hash = generateHash(algo, text);
  openModal(`${algo.toUpperCase()} Hash`, `
    <label style="display:block;margin-bottom:4px;">Result</label>
    <input class="text-input" readonly value="${escapeHtml(hash)}" id="hash-output" />
    <div class="modal-actions">
      <button class="primary" id="hash-copy">Copy</button>
    </div>
  `);
  document.querySelector("#hash-copy")!.addEventListener("click", () => {
    navigator.clipboard.writeText(hash);
    flashStatus(`${algo.toUpperCase()} hash copied`);
    closeModal();
  });
}

document.querySelector("#btn-identify")!.addEventListener("click", () => {
  const selected = tabs.getSelectionOrAll().trim();
  const input = selected.length > 0 && selected.length <= 200 ? selected : prompt("Enter hash to identify:") ?? "";
  if (!input.trim()) return;
  const types = identifyHashTypes(input.trim());
  const result = types.length ? `Possible hash type(s): ${types.join(", ")}` : "Unknown hash type or invalid format";
  openModal("Hash Type Identification", `<p style="font-size:13px;">${escapeHtml(result)}</p>`);
});

document.querySelector("#btn-b64enc")!.addEventListener("click", () => {
  const text = tabs.getSelectionOrAll();
  if (!text.trim()) return flashStatus("No text to encode");
  try {
    tabs.insertAtCursor(base64Encode(text));
    flashStatus("Base64 encoded");
  } catch {
    flashStatus("Could not encode text");
  }
});
document.querySelector("#btn-b64dec")!.addEventListener("click", () => {
  const text = tabs.getSelectionOrAll();
  if (!text.trim()) return flashStatus("No text to decode");
  try {
    tabs.insertAtCursor(base64Decode(text));
    flashStatus("Base64 decoded");
  } catch {
    flashStatus("Could not decode Base64 — invalid input");
  }
});

function flashStatus(msg: string) {
  statusLeft.textContent = msg;
  window.setTimeout(updateStatus, 1800);
}

// ---------------------------------------------------------------------------
// Sidebar: IOCs / Templates / Snippets
// ---------------------------------------------------------------------------
const sidebarTabButtons = document.querySelectorAll<HTMLButtonElement>(".sidebar-tabs button");
sidebarTabButtons.forEach((btn) => {
  btn.addEventListener("click", () => switchSidebar(btn.dataset.panel!));
});
function switchSidebar(panel: string) {
  sidebarTabButtons.forEach((b) => b.classList.toggle("active", b.dataset.panel === panel));
  document.querySelectorAll(".sidebar-panel").forEach((p) => p.classList.toggle("active", p.id === `panel-${panel}`));
}

function renderIocPanel() {
  const container = document.querySelector<HTMLDivElement>("#panel-iocs")!;
  const grouped = groupIocs(lastIocMatches);
  const hasAny = lastIocMatches.length > 0;

  container.innerHTML = `
    <div class="export-row">
      <button id="ioc-csv" ${hasAny ? "" : "disabled"}>CSV</button>
      <button id="ioc-json" ${hasAny ? "" : "disabled"}>JSON</button>
      <button id="ioc-txt" ${hasAny ? "" : "disabled"}>TXT</button>
    </div>
  `;

  if (!hasAny) {
    container.innerHTML += `<p class="ioc-empty">Run "Extract IOCs" to list indicators found in the active tab.</p>`;
    return;
  }

  for (const [type, values] of Object.entries(grouped)) {
    if (values.length === 0) continue;
    const group = document.createElement("div");
    group.className = "ioc-group";
    group.innerHTML = `<h4>${IOC_LABELS[type as keyof typeof IOC_LABELS]} (${values.length})</h4>`;
    for (const v of values) {
      const item = document.createElement("div");
      item.className = "ioc-value";
      item.textContent = v;
      item.title = "Click to copy";
      item.addEventListener("click", () => {
        navigator.clipboard.writeText(v);
        flashStatus(`Copied ${v}`);
      });
      group.appendChild(item);
    }
    container.appendChild(group);
  }

  document.querySelector("#ioc-csv")!.addEventListener("click", () => exportIocsCsv(lastIocMatches));
  document.querySelector("#ioc-json")!.addEventListener("click", () => exportIocsJson(lastIocMatches));
  document.querySelector("#ioc-txt")!.addEventListener("click", () =>
    exportIocsText(Object.fromEntries(Object.entries(grouped).map(([k, v]) => [IOC_LABELS[k as keyof typeof IOC_LABELS], v]))),
  );
}
renderIocPanel();

function renderNamedPanel(
  panelId: string,
  data: Record<string, string>,
  onSave: (data: Record<string, string>) => void,
  onUse: (content: string, name: string) => void,
) {
  const container = document.querySelector<HTMLDivElement>(panelId)!;
  container.innerHTML = `<button id="${panelId.slice(1)}-add" style="width:100%;margin-bottom:8px;">+ New</button>`;

  for (const name of Object.keys(data).sort()) {
    const row = document.createElement("div");
    row.className = "list-item";
    row.style.display = "flex";
    row.style.justifyContent = "space-between";
    row.style.alignItems = "center";
    row.innerHTML = `<span>${escapeHtml(name)}</span>`;
    const del = document.createElement("span");
    del.textContent = "✕";
    del.style.opacity = "0.6";
    del.addEventListener("click", (e) => {
      e.stopPropagation();
      delete data[name];
      onSave(data);
      renderNamedPanel(panelId, data, onSave, onUse);
    });
    row.appendChild(del);
    row.addEventListener("click", () => onUse(fillPlaceholders(data[name]), name));
    container.appendChild(row);
  }

  document.querySelector(`#${panelId.slice(1)}-add`)!.addEventListener("click", () => {
    const name = prompt("Name:");
    if (!name) return;
    const content = prompt("Content:") ?? "";
    data[name] = content;
    onSave(data);
    renderNamedPanel(panelId, data, onSave, onUse);
  });
}

function renderTemplatesPanel() {
  renderNamedPanel(
    "#panel-templates",
    templates,
    (data) => {
      templates = data;
      saveTemplates(templates);
    },
    (content, name) => {
      tabs.createTab(name, content);
      flashStatus(`Opened template: ${name}`);
    },
  );
}
function renderSnippetsPanel() {
  renderNamedPanel(
    "#panel-snippets",
    snippets,
    (data) => {
      snippets = data;
      saveSnippets(snippets);
    },
    (content, name) => {
      tabs.insertAtCursor(content);
      flashStatus(`Inserted snippet: ${name}`);
    },
  );
}
renderTemplatesPanel();
renderSnippetsPanel();

// ---------------------------------------------------------------------------
// Settings + theme
// ---------------------------------------------------------------------------
function updateThemeButton() {
  themeBtn.textContent = settings.darkMode ? "☀️ Light" : "🌙 Dark";
}
updateThemeButton();

function applySettings() {
  document.documentElement.setAttribute("data-theme", settings.darkMode ? "dark" : "light");
  tabs.applySettings(settings);
  saveSettings(settings);
  updateThemeButton();
}

function patchSettings(patch: Partial<Settings>) {
  settings = { ...settings, ...patch };
  applySettings();
}

document.querySelector("#btn-theme")!.addEventListener("click", () => {
  settings = { ...settings, darkMode: !settings.darkMode };
  applySettings();
});

document.querySelector("#btn-settings")!.addEventListener("click", () => {
  openModal(
    "Settings",
    `
    <label>Dark mode <input type="checkbox" id="s-dark" ${settings.darkMode ? "checked" : ""} /></label>
    <label>Line numbers <input type="checkbox" id="s-lines" ${settings.lineNumbers ? "checked" : ""} /></label>
    <label>Word wrap <input type="checkbox" id="s-wrap" ${settings.wordWrap ? "checked" : ""} /></label>
    <label>IOC highlighting <input type="checkbox" id="s-ioc" ${settings.iocHighlighting ? "checked" : ""} /></label>
    <label>Font size <input type="range" min="10" max="22" id="s-font" value="${settings.fontSize}" /></label>
    <div class="modal-actions">
      <button id="s-reset">Reset to defaults</button>
      <button class="primary" id="s-close">Done</button>
    </div>
  `,
  );

  const read = () => ({
    darkMode: (document.querySelector("#s-dark") as HTMLInputElement).checked,
    lineNumbers: (document.querySelector("#s-lines") as HTMLInputElement).checked,
    wordWrap: (document.querySelector("#s-wrap") as HTMLInputElement).checked,
    iocHighlighting: (document.querySelector("#s-ioc") as HTMLInputElement).checked,
    fontSize: Number((document.querySelector("#s-font") as HTMLInputElement).value),
  });
  ["#s-dark", "#s-lines", "#s-wrap", "#s-ioc", "#s-font"].forEach((sel) => {
    document.querySelector(sel)!.addEventListener("input", () => {
      settings = { ...settings, ...read() };
      applySettings();
    });
  });
  document.querySelector("#s-reset")!.addEventListener("click", () => {
    settings = { ...DEFAULT_SETTINGS };
    applySettings();
    closeModal();
  });
  document.querySelector("#s-close")!.addEventListener("click", closeModal);
});

// ---------------------------------------------------------------------------
// Modal helper
// ---------------------------------------------------------------------------
function openModal(title: string, bodyHtml: string, opts?: { wide?: boolean }) {
  closeModal();
  const backdrop = document.createElement("div");
  backdrop.className = "modal-backdrop";
  backdrop.id = "modal-backdrop";
  backdrop.innerHTML = `<div class="modal${opts?.wide ? " modal-wide" : ""}"><h3>${escapeHtml(title)}</h3>${bodyHtml}</div>`;
  backdrop.addEventListener("click", (e) => {
    if (e.target === backdrop) closeModal();
  });
  document.body.appendChild(backdrop);
}
function closeModal() {
  document.querySelector("#modal-backdrop")?.remove();
}

// ---------------------------------------------------------------------------
// Keyboard shortcuts
// ---------------------------------------------------------------------------
document.addEventListener("keydown", (e) => {
  const mod = e.ctrlKey || e.metaKey;
  if (!mod) return;
  switch (e.key.toLowerCase()) {
    case "d":
      e.preventDefault();
      doDefang();
      break;
    case "r":
      e.preventDefault();
      doRefang();
      break;
    case "i":
      e.preventDefault();
      doExtract();
      break;
    case "n":
      e.preventDefault();
      tabs.createTab("Untitled", "");
      break;
    case "w": {
      e.preventDefault();
      const id = tabs.activeTabId();
      if (id) tabs.closeTab(id);
      break;
    }
    case "s": {
      e.preventDefault();
      (document.querySelector("#btn-save") as HTMLButtonElement).click();
      break;
    }
  }
});

// ---------------------------------------------------------------------------
// Phase 3: client contamination checks, training wheels, breakglass, mileage
// ---------------------------------------------------------------------------
phase3Hooks = initPhase3({
  tabs,
  flashStatus,
  openModal,
  closeModal,
  escapeHtml,
  getSettings: () => settings,
  patchSettings,
});

updateStatus();
