// Editor: the polygon editing state machine for one image.
//
// Works entirely in image-pixel coordinates. Knows nothing about the DOM or
// the canvas transform — callers convert screen <-> image via the Viewport and
// hand this class image-space coordinates. Tracks a "dirty" flag so the app
// knows when there is unsaved work.

export class Editor {
  constructor() {
    this.objects = [];   // [{id, label, points:[[x,y],...]}]
    this.draft = null;   // {label, points:[...]} while drawing, else null
    this.selectedId = null;
    this.dirty = false;
  }

  // Replace all state with a freshly loaded annotation (marks clean).
  load(objects) {
    this.objects = objects.map((o) => ({
      id: o.id,
      label: o.label,
      points: o.points.map((p) => [p[0], p[1]]),
    }));
    this.draft = null;
    this.selectedId = null;
    this.dirty = false;
  }

  toObjects() {
    return this.objects.map((o) => ({
      id: o.id,
      label: o.label,
      points: o.points.map((p) => [p[0], p[1]]),
    }));
  }

  // ---- Draft (new polygon) ------------------------------------------------ //

  beginDraft(label) {
    this.draft = { label, points: [] };
    this.selectedId = null;
  }

  get drafting() {
    return this.draft !== null;
  }

  addDraftPoint(x, y) {
    if (!this.draft) return;
    this.draft.points.push([x, y]);
  }

  undoDraftPoint() {
    if (this.draft && this.draft.points.length) this.draft.points.pop();
  }

  canCloseDraft() {
    return !!this.draft && this.draft.points.length >= 3;
  }

  firstDraftPoint() {
    return this.draft && this.draft.points.length ? this.draft.points[0] : null;
  }

  // Finalise the draft into a real object; returns it (or null if too small).
  closeDraft() {
    if (!this.canCloseDraft()) return null;
    const obj = {
      id: newId(),
      label: this.draft.label,
      points: this.draft.points,
    };
    this.objects.push(obj);
    this.draft = null;
    this.selectedId = obj.id;
    this.dirty = true;
    return obj;
  }

  cancelDraft() {
    this.draft = null;
  }

  // ---- Existing objects --------------------------------------------------- //

  select(id) {
    this.selectedId = id;
  }

  getSelected() {
    return this.objects.find((o) => o.id === this.selectedId) || null;
  }

  deleteObject(id) {
    const before = this.objects.length;
    this.objects = this.objects.filter((o) => o.id !== id);
    if (this.selectedId === id) this.selectedId = null;
    if (this.objects.length !== before) this.dirty = true;
  }

  setLabel(id, label) {
    const obj = this.objects.find((o) => o.id === id);
    if (obj && obj.label !== label) {
      obj.label = label;
      this.dirty = true;
    }
  }

  moveVertex(id, index, x, y) {
    const obj = this.objects.find((o) => o.id === id);
    if (obj && obj.points[index]) {
      obj.points[index] = [x, y];
      this.dirty = true;
    }
  }

  // ---- Hit testing (image coordinates) ------------------------------------ //

  // Topmost object containing (x, y), or null.
  hitObject(x, y) {
    for (let i = this.objects.length - 1; i >= 0; i--) {
      if (pointInPolygon(x, y, this.objects[i].points)) return this.objects[i];
    }
    return null;
  }

  // Nearest vertex of the selected object within `radius` (image px), or null.
  hitVertex(x, y, radius) {
    const obj = this.getSelected();
    if (!obj) return null;
    let best = null;
    let bestD = radius;
    obj.points.forEach((p, index) => {
      const d = Math.hypot(p[0] - x, p[1] - y);
      if (d <= bestD) {
        bestD = d;
        best = { id: obj.id, index };
      }
    });
    return best;
  }
}

function newId() {
  if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
  return "obj-" + Math.random().toString(36).slice(2) + Date.now().toString(36);
}

// Ray-casting point-in-polygon test.
export function pointInPolygon(x, y, pts) {
  let inside = false;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const xi = pts[i][0], yi = pts[i][1];
    const xj = pts[j][0], yj = pts[j][1];
    const intersect =
      yi > y !== yj > y &&
      x < ((xj - xi) * (y - yi)) / (yj - yi) + xi;
    if (intersect) inside = !inside;
  }
  return inside;
}
