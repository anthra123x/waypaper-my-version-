/* Waypaper Web UI — single-page app for browsing, previewing, saving wallpapers */

const state = {
  mode: "search",       // "search" | "library"
  page: 1,
  lastPage: 1,
  query: "",
  preset: "random",
  items: [],            // current grid items
  previewItem: null,    // currently previewed item (or null)
  previewPath: null,    // local path of the full-res image
  loading: false,
};

// DOM refs
const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

const grid = $("#grid");
const pagination = $("#pagination");
const statusText = $("#status-text");
const statusCount = $("#status-count");
const searchInput = $("#search-input");
const presetSelect = $("#preset-select");
const btnSearch = $("#btn-search");
const btnLibrary = $("#btn-library");
const previewOverlay = $("#preview-overlay");
const previewImage = $("#preview-image");
const previewLoader = $("#preview-loader");
const previewId = $("#preview-id");
const previewTags = $("#preview-tags");
const btnSet = $("#btn-set");
const btnSave = $("#btn-save");
const btnDiscard = $("#btn-discard");
const btnDelete = $("#btn-delete");
const btnCancel = $("#btn-cancel");

// ── API helpers ────────────────────────────────────────────────────

async function api(url, opts = {}) {
  const res = await fetch(url, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({error: res.statusText}));
    throw new Error(err.error || "Request failed");
  }
  return res.json();
}

// ── Grid rendering ─────────────────────────────────────────────────

function renderGrid() {
  grid.innerHTML = "";
  for (const item of state.items) {
    const el = document.createElement("div");
    el.className = "grid-item";
    if (item.status === "kept") el.classList.add("kept");
    if (item.status === "discarded") el.classList.add("discarded");

    const img = document.createElement("img");
    if (item.thumb_url) {
      img.src = `/api/thumb/${item.id}?url=${encodeURIComponent(item.thumb_url)}`;
    } else if (item.name) {
      img.src = `/api/thumb_local/${item.name}`;
    }
    img.loading = "lazy";
    img.alt = item.id;
    el.appendChild(img);

    const label = document.createElement("div");
    label.className = "item-label";
    label.textContent = item.resolution || item.name || item.id;
    el.appendChild(label);

    el.addEventListener("click", () => openPreview(item));
    grid.appendChild(el);
  }

  statusText.textContent = state.mode === "search"
    ? "Wallhaven " + state.preset
    : "Library";
  statusCount.textContent = `${state.items.length} items`;
}

// ── Pagination ─────────────────────────────────────────────────────

function renderPagination() {
  pagination.innerHTML = `
    <button id="page-prev" ${state.page <= 1 ? "disabled" : ""}>Prev</button>
    <span>${state.page} / ${state.lastPage}</span>
    <button id="page-next" ${state.page >= state.lastPage ? "disabled" : ""}>Next</button>
  `;
  $("#page-prev")?.addEventListener("click", () => goToPage(state.page - 1));
  $("#page-next")?.addEventListener("click", () => goToPage(state.page + 1));
}

// ── Data loading ───────────────────────────────────────────────────

async function loadSearch(preset, query, page) {
  state.loading = true;
  statusText.textContent = "Loading…";
  try {
    const params = new URLSearchParams({preset, page: String(page)});
    if (query) params.set("q", query);
    const data = await api(`/api/search?${params}`);
    state.items = data.items.map(i => ({...i, status: null}));
    state.page = data.page;
    state.lastPage = data.last_page;

    // Check brain status for each item
    for (const item of state.items) {
      try {
        const s = await api(`/api/status?id=${item.id}`);
        item.status = s.status;
      } catch {}
    }
  } catch (err) {
    statusText.textContent = "Error: " + err.message;
  }
  state.loading = false;
  renderGrid();
  renderPagination();
}

async function loadLibrary() {
  state.loading = true;
  statusText.textContent = "Loading…";
  try {
    const data = await api("/api/library");
    state.items = data.items.map(i => ({
      id: i.id,
      name: i.name,
      path: i.path,
      resolution: "",
      tags: [],
      status: i.status,
      thumb_url: null,
    }));
    state.page = 1;
    state.lastPage = 1;
  } catch (err) {
    statusText.textContent = "Error: " + err.message;
  }
  state.loading = false;
  renderGrid();
  renderPagination();
}

function goToPage(page) {
  if (page < 1 || page > state.lastPage || state.loading) return;
  if (state.mode === "search") {
    loadSearch(state.preset, state.query, page);
  }
}

// ── Mode switching ──────────────────────────────────────────────────

function setMode(mode) {
  state.mode = mode;
  btnSearch.classList.toggle("active", mode === "search");
  btnLibrary.classList.toggle("active", mode === "library");
  searchInput.disabled = mode !== "search";
  presetSelect.disabled = mode !== "search";

  if (mode === "search") {
    loadSearch(state.preset, state.query, 1);
  } else {
    loadLibrary();
  }
}

// ── Preview modal ───────────────────────────────────────────────────

async function openPreview(item) {
  state.previewItem = item;
  previewOverlay.classList.remove("hidden");
  previewImage.src = "";
  previewLoader.classList.remove("hidden");
  previewId.textContent = item.id;
  previewTags.textContent = "";
  btnDelete.classList.add("hidden");

  // Show/hide buttons based on mode
  if (state.mode === "library") {
    btnSet.classList.add("hidden");
    btnSave.classList.add("hidden");
    btnDelete.classList.remove("hidden");
    btnDiscard.classList.remove("hidden");

    // Load local file as preview
    if (item.name) {
      previewImage.src = `/api/thumb_local/${item.name}`;
      previewImage.onload = () => previewLoader.classList.add("hidden");
    }
  } else {
    btnSet.classList.remove("hidden");
    btnSave.classList.remove("hidden");
    btnDelete.classList.add("hidden");
    btnDiscard.classList.remove("hidden");

    // Download full-res to temp
    try {
      const data = await api("/api/download/" + item.id, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({full_url: item.full_url}),
      });
      state.previewPath = data.path;
      const ts = Date.now();
      previewImage.src = "/api/temp/wh-" + item.id + "?t=" + ts;
      previewImage.onload = () => previewLoader.classList.add("hidden");
    } catch (err) {
      previewLoader.textContent = "Download failed: " + err.message;
    }
  }

  // Tags
  if (item.tags && item.tags.length) {
    previewTags.textContent = "Tags: " + item.tags.slice(0, 8).join(", ");
  }
}

function closePreview() {
  previewOverlay.classList.add("hidden");
  state.previewItem = null;
  state.previewPath = null;
}

// ── Preview actions ────────────────────────────────────────────────

btnSet.addEventListener("click", async () => {
  const item = state.previewItem;
  if (!item) return;
  try {
    await api("/api/set/" + item.id, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({full_url: item.full_url}),
    });
    statusText.textContent = "Wallpaper set!";
    closePreview();
  } catch (err) {
    statusText.textContent = "Error: " + err.message;
  }
});

btnSave.addEventListener("click", async () => {
  const item = state.previewItem;
  if (!item) return;
  try {
    await api("/api/save/" + item.id, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({full_url: item.full_url}),
    });
    statusText.textContent = "Saved to library!";
    closePreview();
  } catch (err) {
    statusText.textContent = "Error: " + err.message;
  }
});

btnDiscard.addEventListener("click", async () => {
  const item = state.previewItem;
  if (!item) return;
  try {
    const body = state.mode === "library"
      ? JSON.stringify({path: item.path})
      : JSON.stringify({full_url: item.full_url});

    await api("/api/discard/" + item.id, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body,
    });
    statusText.textContent = "Discarded";
    closePreview();
    if (state.mode === "library") loadLibrary();
    else loadSearch(state.preset, state.query, state.page);
  } catch (err) {
    statusText.textContent = "Error: " + err.message;
  }
});

btnDelete.addEventListener("click", async () => {
  const item = state.previewItem;
  if (!item) return;
  if (!confirm(`Delete ${item.name} from library?`)) return;
  try {
    await api("/api/library/" + item.id, {method: "DELETE"});
    statusText.textContent = "Deleted";
    closePreview();
    loadLibrary();
  } catch (err) {
    statusText.textContent = "Error: " + err.message;
  }
});

btnCancel.addEventListener("click", closePreview);
previewOverlay.addEventListener("click", (e) => {
  if (e.target === previewOverlay) closePreview();
});

// ── Keyboard shortcuts ─────────────────────────────────────────────

document.addEventListener("keydown", (e) => {
  // Ignore if typing in input
  if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;

  if (state.previewItem) {
    // Preview is open
    if (e.key === "Escape") closePreview();
    else if (e.key === "Enter" && state.mode === "search") btnSet.click();
    else if (e.key === "d" || e.key === "D") btnDiscard.click();
    else if (e.key === "s" || e.key === "S") btnSave.click();
    else if (e.key === "y" || e.key === "Y") btnDelete.click();
    else if (e.key === "k" || e.key === "K") closePreview();
  } else {
    if (e.key === "1") setMode("search");
    else if (e.key === "2") setMode("library");
    else if (e.key === "r" || e.key === "R") {
      if (state.mode === "search") loadSearch(state.preset, state.query, 1);
      else loadLibrary();
    }
    // Grid navigation
    else if (e.key === "j" || e.key === "J") {
      const items = $$(".grid-item");
      const focused = document.activeElement?.closest(".grid-item");
      const idx = focused ? Array.from(items).indexOf(focused) : -1;
      const next = items[Math.min(idx + 1, items.length - 1)];
      if (next) { next.focus(); next.scrollIntoView({block: "nearest"}); }
    }
    else if (e.key === "k" || e.key === "K") {
      const items = $$(".grid-item");
      const focused = document.activeElement?.closest(".grid-item");
      const idx = focused ? Array.from(items).indexOf(focused) : items.length;
      const prev = items[Math.max(idx - 1, 0)];
      if (prev) { prev.focus(); prev.scrollIntoView({block: "nearest"}); }
    }
    else if (e.key === "ArrowLeft") {
      const prev = document.getElementById("page-prev");
      if (prev && !prev.disabled) prev.click();
    }
    else if (e.key === "ArrowRight") {
      const next = document.getElementById("page-next");
      if (next && !next.disabled) next.click();
    }
  }
});

// ── Event bindings ──────────────────────────────────────────────────

btnSearch.addEventListener("click", () => setMode("search"));
btnLibrary.addEventListener("click", () => setMode("library"));

let searchTimer = null;
searchInput.addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    state.query = searchInput.value.trim();
    loadSearch(state.preset, state.query, 1);
  }, 400);
});

presetSelect.addEventListener("change", () => {
  state.preset = presetSelect.value;
  loadSearch(state.preset, state.query, 1);
});

// ── Init ────────────────────────────────────────────────────────────

presetSelect.value = state.preset;
setMode("search");
