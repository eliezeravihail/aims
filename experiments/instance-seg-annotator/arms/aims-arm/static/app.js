// App — in-memory state, image navigation, class selection, and wiring. Owns no drawing math (that is
// canvas.js) and no URLs (that is api.js).
import { api } from "./api.js";
import { AnnotatorCanvas } from "./canvas.js";

const el = (id) => document.getElementById(id);

const state = {
  images: [],
  index: 0,
  classes: [],        // [{name,color}]
  activeClass: null,
  objects: [],        // current image's finished objects
  dirty: false,
};

let canvas;

function colorMap() {
  return Object.fromEntries(state.classes.map((c) => [c.name, c.color]));
}

// ── image navigation ────────────────────────────────────────────────────────
async function loadImage(index) {
  if (!state.images.length) return;
  state.index = (index + state.images.length) % state.images.length;
  const id = state.images[state.index];
  const ann = await api.getAnnotations(id);
  state.objects = ann.objects;
  state.dirty = false;

  const img = new Image();
  img.onload = () => {
    canvas.setImage(img, ann.width, ann.height);
    canvas.setObjects(state.objects);
    renderObjectList();
  };
  img.src = api.rawImageUrl(id);
  el("position").textContent = `${state.index + 1} / ${state.images.length} — ${id}`;
  renderObjectList();
}

async function save() {
  if (!state.images.length) return;
  const id = state.images[state.index];
  const saved = await api.putAnnotations(id, state.objects);
  state.objects = saved.objects;
  state.dirty = false;
  flash("Saved");
  renderObjectList();
}

async function navigate(delta) {
  if (state.dirty) await save();
  await loadImage(state.index + delta);
}

// ── object list ───────────────────────────────────────────────────────────--
function renderObjectList() {
  const list = el("objects");
  list.innerHTML = "";
  state.objects.forEach((obj, i) => {
    const row = document.createElement("li");
    const swatch = document.createElement("span");
    swatch.className = "swatch";
    swatch.style.background = colorMap()[obj.class] || "#9aa0a6";
    const label = document.createElement("span");
    label.textContent = `${obj.class} (${obj.polygon.length} pts)`;
    const del = document.createElement("button");
    del.textContent = "×";
    del.title = "delete object";
    del.onclick = () => {
      state.objects.splice(i, 1);
      state.dirty = true;
      canvas.setObjects(state.objects);
      renderObjectList();
    };
    row.append(swatch, label, del);
    list.append(row);
  });
  el("obj-count").textContent = String(state.objects.length);
}

// ── class list ────────────────────────────────────────────────────────────--
function renderClassBar() {
  const bar = el("classes");
  bar.innerHTML = "";
  state.classes.forEach((c) => {
    const b = document.createElement("button");
    b.className = "class-btn" + (c.name === state.activeClass ? " active" : "");
    b.style.borderColor = c.color;
    b.innerHTML = `<span class="swatch" style="background:${c.color}"></span>${c.name}`;
    b.onclick = () => {
      state.activeClass = c.name;
      canvas.setActiveClass(c.name);
      renderClassBar();
    };
    bar.append(b);
  });
  canvas.setClasses(colorMap());
}

function renderClassEditor() {
  const box = el("class-editor-rows");
  box.innerHTML = "";
  state.classes.forEach((c, i) => {
    const row = document.createElement("div");
    row.className = "editor-row";
    const name = document.createElement("input");
    name.value = c.name;
    name.oninput = () => (state.classes[i].name = name.value);
    const color = document.createElement("input");
    color.type = "color";
    color.value = c.color;
    color.oninput = () => (state.classes[i].color = color.value);
    const del = document.createElement("button");
    del.textContent = "×";
    del.onclick = () => { state.classes.splice(i, 1); renderClassEditor(); };
    row.append(name, color, del);
    box.append(row);
  });
}

async function saveClasses() {
  state.classes = await api.putClasses(state.classes);
  if (!state.classes.some((c) => c.name === state.activeClass)) {
    state.activeClass = state.classes.length ? state.classes[0].name : null;
    canvas.setActiveClass(state.activeClass);
  }
  renderClassBar();
  renderClassEditor();
  renderObjectList();
  flash("Classes saved");
}

// ── export ────────────────────────────────────────────────────────────────--
async function exportTiles() {
  if (state.dirty) await save();
  const tile_size = parseInt(prompt("Tile size (px)?", "1024"), 10);
  if (!tile_size) return;
  const overlap = parseInt(prompt("Overlap between tiles (px)?", "128"), 10);
  if (Number.isNaN(overlap)) return;
  const name = (prompt("Dataset name?", "dataset") || "").trim();
  if (!name) return;
  try {
    const s = await api.exportDataset({ tile_size, overlap, name });
    flash(`Exported ${s.tiles} tiles, ${s.instances} instances → .exports/${s.name}`);
  } catch (e) {
    flash(String(e.message || e));
  }
}

// ── misc ui ─────────────────────────────────────────────────────────────────
let flashTimer;
function flash(msg) {
  const n = el("flash");
  n.textContent = msg;
  clearTimeout(flashTimer);
  flashTimer = setTimeout(() => (n.textContent = ""), 1500);
}

function wireKeys() {
  window.addEventListener("keydown", (e) => {
    if (e.target.tagName === "INPUT") return;
    if (e.key === "Enter") { if (canvas.closeDraft()) state.dirty = true; renderObjectList(); }
    else if (e.key === "Escape") canvas.cancelDraft();
    else if (e.key === "Backspace") { e.preventDefault(); canvas.undoDraftVertex(); }
    else if (e.key === "s" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); save(); }
    else if (e.key === "ArrowRight") navigate(1);
    else if (e.key === "ArrowLeft") navigate(-1);
  });
}

async function main() {
  canvas = new AnnotatorCanvas(el("canvas"), {
    onObjectsChanged: (objs) => { state.objects = objs; state.dirty = true; renderObjectList(); },
  });

  el("prev").onclick = () => navigate(-1);
  el("next").onclick = () => navigate(1);
  el("save").onclick = () => save();
  el("export").onclick = () => exportTiles();
  el("add-class").onclick = () => { state.classes.push({ name: "new", color: "#ff3860" }); renderClassEditor(); };
  el("save-classes").onclick = () => saveClasses();
  el("toggle-editor").onclick = () => el("class-editor").classList.toggle("hidden");

  state.classes = await api.getClasses();
  state.activeClass = state.classes.length ? state.classes[0].name : null;
  canvas.setActiveClass(state.activeClass);
  renderClassBar();
  renderClassEditor();

  state.images = await api.listImages();
  if (!state.images.length) {
    el("position").textContent = "No PNG/JPEG images in the mounted folder.";
    return;
  }
  wireKeys();
  await loadImage(0);
}

main();
