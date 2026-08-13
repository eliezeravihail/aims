// App: orchestration and event wiring. Holds the running state (image list,
// current image, editor, viewport), translates DOM events into editor actions,
// and drives navigation + saving. Delegates all drawing to render.js, all
// polygon logic to editor.js, and all persistence to api.js.

import { api } from "./api.js";
import { Viewport } from "./viewport.js";
import { Editor } from "./editor.js";
import { render } from "./render.js";
import { ClassPanel } from "./classes.js";

const VERTEX_GRAB_PX = 7;    // screen-px radius to grab a vertex
const CLOSE_SNAP_PX = 10;    // screen-px radius to close on the first point

const canvas = document.getElementById("canvas");
const viewport = new Viewport(canvas);
const editor = new Editor();

const state = {
  images: [],          // [{name, width, height, object_count}]
  index: -1,
  image: null,         // HTMLImageElement of current image
  cursorScreen: null,  // [x, y] for rubber-band line
  panning: null,       // {x, y} last pan point
  draggingVertex: null // {id, index}
};

const classPanel = new ClassPanel(document.getElementById("class-panel"), {
  onChange: () => {
    renderObjectList();
    scheduleRender();
  },
});

// --------------------------------------------------------------------------- //
// Boot
// --------------------------------------------------------------------------- //

async function boot() {
  await classPanel.load();
  state.images = await api.listImages();
  renderImageList();
  wireEvents();
  window.addEventListener("resize", onResize);
  onResize();
  if (state.images.length) await goTo(0);
  else setPosition();
}

// --------------------------------------------------------------------------- //
// Navigation
// --------------------------------------------------------------------------- //

async function goTo(index) {
  if (index < 0 || index >= state.images.length) return;
  if (editor.dirty) await save();          // never lose work on navigation
  state.index = index;
  const info = state.images[index];

  editor.cancelDraft();
  const ann = await api.getAnnotation(info.name);
  editor.load(ann.objects);

  await loadImageElement(info.name, ann.width, ann.height);
  markClean();
  renderImageList();
  renderObjectList();
  setPosition();
}

function loadImageElement(name, w, h) {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      state.image = img;
      viewport.fit(img.naturalWidth || w, img.naturalHeight || h);
      scheduleRender();
      resolve();
    };
    img.onerror = () => {
      state.image = null;
      viewport.fit(w, h);
      scheduleRender();
      resolve();
    };
    img.src = api.imageFileUrl(name);
  });
}

function currentName() {
  return state.index >= 0 ? state.images[state.index].name : null;
}

// --------------------------------------------------------------------------- //
// Saving
// --------------------------------------------------------------------------- //

async function save() {
  const name = currentName();
  if (!name) return;
  const info = state.images[state.index];
  const annotation = {
    image: name,
    width: info.width,
    height: info.height,
    objects: editor.toObjects(),
  };
  const saved = await api.saveAnnotation(name, annotation);
  info.object_count = saved.objects.length;
  markClean();
  renderImageList();
}

function markClean() {
  editor.dirty = false;
  document.getElementById("dirty-flag").classList.add("hidden");
}

function markDirtyIfNeeded() {
  document.getElementById("dirty-flag").classList.toggle("hidden", !editor.dirty);
}

// --------------------------------------------------------------------------- //
// Tiled dataset export
// --------------------------------------------------------------------------- //

async function exportDataset() {
  if (editor.dirty) await save();  // export the latest annotations
  const tileSize = parseInt(prompt("Tile size (px):", "512"), 10);
  if (!tileSize) return;
  const overlap = parseInt(prompt("Overlap between tiles (px):", "64"), 10);
  if (Number.isNaN(overlap)) return;
  if (overlap >= tileSize) {
    alert("Overlap must be smaller than the tile size.");
    return;
  }
  // Let the browser stream the zip straight to the user's downloads.
  window.location = api.exportUrl(tileSize, overlap);
}

// --------------------------------------------------------------------------- //
// Canvas interaction
// --------------------------------------------------------------------------- //

function mousePos(evt) {
  const rect = canvas.getBoundingClientRect();
  return [evt.clientX - rect.left, evt.clientY - rect.top];
}

function onMouseDown(evt) {
  const [sx, sy] = mousePos(evt);

  // Right / middle button -> pan.
  if (evt.button === 2 || evt.button === 1) {
    state.panning = { x: sx, y: sy };
    evt.preventDefault();
    return;
  }
  if (evt.button !== 0) return;

  const [ix, iy] = viewport.screenToImage(sx, sy);

  if (editor.drafting) {
    const first = editor.firstDraftPoint();
    if (first && editor.canCloseDraft()) {
      const [fsx, fsy] = viewport.imageToScreen(first[0], first[1]);
      if (Math.hypot(fsx - sx, fsy - sy) <= CLOSE_SNAP_PX) {
        closeDraft();
        return;
      }
    }
    editor.addDraftPoint(ix, iy);
    scheduleRender();
    return;
  }

  // Not drafting: try to grab a vertex of the selected object.
  const v = editor.hitVertex(ix, iy, VERTEX_GRAB_PX / viewport.scale);
  if (v) {
    state.draggingVertex = v;
    return;
  }

  // Select an object under the cursor, else start a new polygon.
  const hit = editor.hitObject(ix, iy);
  if (hit) {
    editor.select(hit.id);
    renderObjectList();
    scheduleRender();
    return;
  }

  const label = classPanel.activeLabel();
  if (!label) {
    alert("Add a class first (right panel) before drawing.");
    return;
  }
  editor.beginDraft(label);
  editor.addDraftPoint(ix, iy);
  scheduleRender();
}

function onMouseMove(evt) {
  const [sx, sy] = mousePos(evt);
  state.cursorScreen = [sx, sy];

  if (state.panning) {
    viewport.panBy(sx - state.panning.x, sy - state.panning.y);
    state.panning = { x: sx, y: sy };
    scheduleRender();
    return;
  }

  if (state.draggingVertex) {
    const [ix, iy] = viewport.screenToImage(sx, sy);
    editor.moveVertex(state.draggingVertex.id, state.draggingVertex.index, ix, iy);
    markDirtyIfNeeded();
    scheduleRender();
    return;
  }

  if (editor.drafting) scheduleRender();  // update rubber-band line
}

function onMouseUp(evt) {
  if (state.panning) state.panning = null;
  if (state.draggingVertex) state.draggingVertex = null;
}

function onWheel(evt) {
  evt.preventDefault();
  const [sx, sy] = mousePos(evt);
  const factor = evt.deltaY < 0 ? 1.1 : 1 / 1.1;
  viewport.zoomAt(sx, sy, factor);
  scheduleRender();
}

function closeDraft() {
  const obj = editor.closeDraft();
  if (obj) {
    markDirtyIfNeeded();
    renderObjectList();
    renderImageList();
  }
  scheduleRender();
}

function onKeyDown(evt) {
  const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName);
  if (typing) return;

  if ((evt.ctrlKey || evt.metaKey) && evt.key.toLowerCase() === "s") {
    evt.preventDefault();
    save();
    return;
  }
  switch (evt.key) {
    case "Enter":
      if (editor.canCloseDraft()) { closeDraft(); evt.preventDefault(); }
      break;
    case "Escape":
      if (editor.drafting) { editor.cancelDraft(); scheduleRender(); }
      break;
    case "Backspace":
      if (editor.drafting) { editor.undoDraftPoint(); scheduleRender(); evt.preventDefault(); }
      break;
    case "Delete":
      if (editor.selectedId) {
        editor.deleteObject(editor.selectedId);
        markDirtyIfNeeded();
        renderObjectList();
        renderImageList();
        scheduleRender();
      }
      break;
    case "[":
      goTo(state.index - 1);
      break;
    case "]":
      goTo(state.index + 1);
      break;
  }
}

// --------------------------------------------------------------------------- //
// Sidebar rendering
// --------------------------------------------------------------------------- //

function renderImageList() {
  const ul = document.getElementById("image-list");
  ul.innerHTML = "";
  state.images.forEach((info, i) => {
    const li = document.createElement("li");
    if (i === state.index) li.className = "active";
    const name = document.createElement("span");
    name.className = "name";
    name.textContent = info.name;
    const count = document.createElement("span");
    count.className = "count";
    count.textContent = info.object_count;
    li.append(name, count);
    li.addEventListener("click", () => goTo(i));
    ul.appendChild(li);
  });
}

function renderObjectList() {
  const ul = document.getElementById("object-list");
  ul.innerHTML = "";
  editor.objects.forEach((obj) => {
    const li = document.createElement("li");
    if (obj.id === editor.selectedId) li.className = "active";

    const dot = document.createElement("span");
    dot.className = "dot";
    dot.style.background = classPanel.colorFor(obj.label);

    const sel = document.createElement("select");
    for (const c of classPanel.classes) {
      const opt = document.createElement("option");
      opt.value = c.name;
      opt.textContent = c.name;
      if (c.name === obj.label) opt.selected = true;
      sel.appendChild(opt);
    }
    // Label may reference a deleted class; show it so it is not lost.
    if (!classPanel.classes.some((c) => c.name === obj.label)) {
      const opt = document.createElement("option");
      opt.value = obj.label;
      opt.textContent = obj.label + " (removed)";
      opt.selected = true;
      sel.appendChild(opt);
    }
    sel.addEventListener("change", (e) => {
      editor.setLabel(obj.id, e.target.value);
      dot.style.background = classPanel.colorFor(e.target.value);
      markDirtyIfNeeded();
      scheduleRender();
    });

    const del = document.createElement("button");
    del.className = "obj-del";
    del.textContent = "×";
    del.title = "Delete object";
    del.addEventListener("click", (e) => {
      e.stopPropagation();
      editor.deleteObject(obj.id);
      markDirtyIfNeeded();
      renderObjectList();
      renderImageList();
      scheduleRender();
    });

    li.append(dot, sel, del);
    li.addEventListener("click", (e) => {
      if (e.target === sel || e.target === del) return;
      editor.select(obj.id);
      renderObjectList();
      scheduleRender();
    });
    ul.appendChild(li);
  });
  document.getElementById("object-count").textContent = editor.objects.length;
}

function setPosition() {
  const pos = document.getElementById("image-position");
  const nameEl = document.getElementById("current-name");
  if (state.index < 0) {
    pos.textContent = state.images.length ? "–" : "0 / 0";
    nameEl.textContent = state.images.length ? "No image selected" : "No images in folder";
  } else {
    pos.textContent = `${state.index + 1} / ${state.images.length}`;
    nameEl.textContent = currentName();
  }
  document.getElementById("prev-btn").disabled = state.index <= 0;
  document.getElementById("next-btn").disabled = state.index >= state.images.length - 1;
}

// --------------------------------------------------------------------------- //
// Render scheduling + wiring
// --------------------------------------------------------------------------- //

let rafPending = false;
function scheduleRender() {
  markDirtyIfNeeded();
  if (rafPending) return;
  rafPending = true;
  requestAnimationFrame(() => {
    rafPending = false;
    render(viewport, state.image, editor, (l) => classPanel.colorFor(l),
           editor.drafting ? state.cursorScreen : null);
  });
}

function onResize() {
  viewport.syncSize();
  if (state.image) {
    // Keep the image fitted on resize (simple + predictable).
    viewport.fit(viewport.imgW, viewport.imgH);
  }
  scheduleRender();
}

function wireEvents() {
  canvas.addEventListener("mousedown", onMouseDown);
  window.addEventListener("mousemove", onMouseMove);
  window.addEventListener("mouseup", onMouseUp);
  canvas.addEventListener("wheel", onWheel, { passive: false });
  canvas.addEventListener("contextmenu", (e) => e.preventDefault());
  window.addEventListener("keydown", onKeyDown);

  document.getElementById("prev-btn").addEventListener("click", () => goTo(state.index - 1));
  document.getElementById("next-btn").addEventListener("click", () => goTo(state.index + 1));
  document.getElementById("save-btn").addEventListener("click", save);
  document.getElementById("export-btn").addEventListener("click", exportDataset);

  window.addEventListener("beforeunload", (e) => {
    if (editor.dirty) { e.preventDefault(); e.returnValue = ""; }
  });
}

boot().catch((err) => {
  console.error(err);
  alert("Failed to start the annotator: " + err.message);
});
