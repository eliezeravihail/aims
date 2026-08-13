// Canvas annotator UI. Owns rendering and pointer interaction only.
// Annotation geometry is held and sent in ORIGINAL-IMAGE PIXELS; every pointer
// sample is funneled through coords.viewportToImage before it becomes a vertex,
// and the viewport transform is used solely for painting. Persistence and
// validation live on the server (app/storage.py, app/model.py).

import {
  makeTransform, imageToViewport, viewportToImage, zoomed, panned, fitTransform,
} from "/coords.js";

const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");

const state = {
  images: [],
  index: 0,
  meta: null,            // { image, width, height }
  imgEl: null,           // HTMLImageElement of current image
  transform: makeTransform(),
  classes: [],           // [{id,name,color}]
  classById: {},
  instances: [],         // [{ class_id, vertices: [[x,y],...] }]  image-space
  draft: [],             // in-progress polygon vertices, image-space
  selected: -1,          // selected instance index
  dirty: false,
};

// --- data loading ---------------------------------------------------------

async function boot() {
  const cfg = await (await fetch("/api/config")).json();
  state.classes = cfg.classes;
  state.classById = Object.fromEntries(cfg.classes.map((c) => [c.id, c]));
  const sel = document.getElementById("classSelect");
  sel.innerHTML = state.classes.map((c) => `<option value="${c.id}">${c.name}</option>`).join("");

  const list = await (await fetch("/api/images")).json();
  state.images = list.images;
  if (state.images.length === 0) {
    setStatus("No images in input folder.");
    return;
  }
  await loadImage(0);
}

async function loadImage(i) {
  if (i < 0 || i >= state.images.length) return;
  state.index = i;
  const name = state.images[i];
  document.getElementById("imageName").textContent = `${name} (${i + 1}/${state.images.length})`;

  const doc = await (await fetch(`/api/annotations/${encodeURIComponent(name)}`)).json();
  state.meta = { image: doc.image, width: doc.width, height: doc.height };
  state.instances = doc.instances.map((ins) => ({
    class_id: ins.class_id,
    vertices: ins.vertices.map(([x, y]) => [x, y]),
  }));
  state.draft = [];
  state.selected = -1;
  state.dirty = false;

  state.imgEl = new Image();
  state.imgEl.onload = () => { fitView(); render(); };
  state.imgEl.src = `/api/images/${encodeURIComponent(name)}/raw`;
  renderInstanceList();
  setStatus("Loaded.");
}

// --- geometry actions -----------------------------------------------------

function currentClassId() {
  return document.getElementById("classSelect").value;
}

function finishPolygon() {
  if (state.draft.length < 3) {
    setStatus("Need at least 3 vertices to close a polygon.");
    return;
  }
  state.instances.push({ class_id: currentClassId(), vertices: state.draft });
  state.draft = [];
  state.dirty = true;
  renderInstanceList();
  render();
  setStatus("Instance added.");
}

function cancelDraft() {
  state.draft = [];
  render();
}

function deleteInstance(idx) {
  state.instances.splice(idx, 1);
  if (state.selected === idx) state.selected = -1;
  state.dirty = true;
  renderInstanceList();
  render();
}

async function save() {
  if (!state.meta) return;
  const body = {
    image: state.meta.image,
    width: state.meta.width,
    height: state.meta.height,
    instances: state.instances,
  };
  const res = await fetch(`/api/annotations/${encodeURIComponent(state.meta.image)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (res.ok) {
    state.dirty = false;
    setStatus("Saved.");
  } else {
    const err = await res.json().catch(() => ({}));
    setStatus(`Save failed: ${err.detail || res.status}`);
  }
}

// --- view / rendering -----------------------------------------------------

function resizeCanvas() {
  const wrap = document.getElementById("canvasWrap");
  const dpr = window.devicePixelRatio || 1;
  canvas.width = wrap.clientWidth * dpr;
  canvas.height = wrap.clientHeight * dpr;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

function viewSize() {
  const dpr = window.devicePixelRatio || 1;
  return [canvas.width / dpr, canvas.height / dpr];
}

function fitView() {
  if (!state.meta) return;
  const [vw, vh] = viewSize();
  state.transform = fitTransform(state.meta.width, state.meta.height, vw, vh);
}

function render() {
  const [vw, vh] = viewSize();
  ctx.clearRect(0, 0, vw, vh);
  if (!state.imgEl || !state.meta) return;

  const t = state.transform;
  ctx.save();
  ctx.setTransform((window.devicePixelRatio || 1) * t.scale, 0, 0,
                   (window.devicePixelRatio || 1) * t.scale, 0, 0);
  ctx.translate(t.tx / t.scale, t.ty / t.scale);
  ctx.drawImage(state.imgEl, 0, 0);
  ctx.restore();

  state.instances.forEach((ins, idx) => drawPolygon(ins.vertices, colorFor(ins.class_id),
    idx === state.selected, true));
  if (state.draft.length > 0) {
    drawPolygon(state.draft, colorFor(currentClassId()), false, false);
  }
}

function drawPolygon(verts, color, selected, closed) {
  if (verts.length === 0) return;
  const pts = verts.map((p) => imageToViewport(p, state.transform));
  ctx.lineWidth = selected ? 3 : 2;
  ctx.strokeStyle = color;
  ctx.fillStyle = hexToRgba(color, 0.25);
  ctx.beginPath();
  pts.forEach(([x, y], i) => (i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)));
  if (closed) ctx.closePath();
  if (closed) ctx.fill();
  ctx.stroke();
  // vertex dots
  ctx.fillStyle = color;
  pts.forEach(([x, y]) => { ctx.beginPath(); ctx.arc(x, y, 3.5, 0, Math.PI * 2); ctx.fill(); });
}

function renderInstanceList() {
  const ul = document.getElementById("instanceList");
  ul.innerHTML = "";
  state.instances.forEach((ins, idx) => {
    const c = state.classById[ins.class_id];
    const li = document.createElement("li");
    if (idx === state.selected) li.classList.add("selected");
    li.innerHTML = `
      <span class="swatch" style="background:${colorFor(ins.class_id)}"></span>
      <span class="iname">${c ? c.name : ins.class_id} · ${ins.vertices.length} pts</span>
      <button class="del">✕</button>`;
    li.querySelector(".iname").onclick = () => {
      state.selected = idx; renderInstanceList(); render();
    };
    li.querySelector(".del").onclick = (e) => { e.stopPropagation(); deleteInstance(idx); };
    ul.appendChild(li);
  });
}

function colorFor(classId) {
  const c = state.classById[classId];
  return c ? c.color : "#888888";
}

function hexToRgba(hex, a) {
  const m = hex.replace("#", "");
  const n = parseInt(m.length === 3 ? m.split("").map((x) => x + x).join("") : m, 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
}

function setStatus(msg) {
  document.getElementById("status").textContent = msg;
}

// --- pointer + keyboard ---------------------------------------------------

function canvasPoint(ev) {
  const r = canvas.getBoundingClientRect();
  return [ev.clientX - r.left, ev.clientY - r.top];
}

let panning = null;

canvas.addEventListener("mousedown", (ev) => {
  if (ev.button === 1) { // middle: pan
    panning = canvasPoint(ev);
    ev.preventDefault();
  } else if (ev.button === 0) { // left: add vertex (in image space)
    const vpt = canvasPoint(ev);
    state.draft.push(viewportToImage(vpt, state.transform));
    render();
  }
});

window.addEventListener("mousemove", (ev) => {
  if (panning) {
    const [x, y] = canvasPoint(ev);
    state.transform = panned(state.transform, x - panning[0], y - panning[1]);
    panning = [x, y];
    render();
  }
});

window.addEventListener("mouseup", () => { panning = null; });

canvas.addEventListener("contextmenu", (ev) => ev.preventDefault());

canvas.addEventListener("wheel", (ev) => {
  ev.preventDefault();
  const factor = ev.deltaY < 0 ? 1.1 : 1 / 1.1;
  state.transform = zoomed(state.transform, factor, canvasPoint(ev));
  render();
}, { passive: false });

canvas.addEventListener("dblclick", () => finishPolygon());

window.addEventListener("keydown", (ev) => {
  if (ev.key === "Enter") finishPolygon();
  else if (ev.key === "Escape") cancelDraft();
});

// --- wiring ---------------------------------------------------------------

document.getElementById("prevBtn").onclick = () => loadImage(state.index - 1);
document.getElementById("nextBtn").onclick = () => loadImage(state.index + 1);
document.getElementById("finishBtn").onclick = finishPolygon;
document.getElementById("cancelBtn").onclick = cancelDraft;
document.getElementById("fitBtn").onclick = () => { fitView(); render(); };
document.getElementById("saveBtn").onclick = save;

window.addEventListener("resize", () => { resizeCanvas(); render(); });

resizeCanvas();
boot();
