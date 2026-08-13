// Canvas layer — the SINGLE owner of the display<->image coordinate transform and all polygon
// rendering/drawing. Only image-space coordinates ever leave this module, so nothing the app or
// server sees is ever in display/canvas pixels.

export class AnnotatorCanvas {
  constructor(canvasEl, { onObjectsChanged }) {
    this.canvas = canvasEl;
    this.ctx = canvasEl.getContext("2d");
    this.onObjectsChanged = onObjectsChanged || (() => {});

    this.img = null;          // HTMLImageElement
    this.imgW = 0;
    this.imgH = 0;
    this.objects = [];        // finished: [{class, polygon:[[x,y],...]}]  (image space)
    this.draft = [];          // in-progress vertices (image space)
    this.classColors = {};    // name -> color
    this.activeClass = null;

    this._scale = 1;
    this._ox = 0;             // letterbox offset (canvas px)
    this._oy = 0;

    this.canvas.addEventListener("click", (e) => this._onClick(e));
    this.canvas.addEventListener("dblclick", (e) => { e.preventDefault(); this.closeDraft(); });
    window.addEventListener("resize", () => this._fitAndDraw());
  }

  // ── transform (the owned responsibility) ──────────────────────────────────
  _fit() {
    const cw = this.canvas.clientWidth;
    const ch = this.canvas.clientHeight;
    this.canvas.width = cw;
    this.canvas.height = ch;
    if (!this.imgW || !this.imgH) return;
    this._scale = Math.min(cw / this.imgW, ch / this.imgH);
    this._ox = (cw - this.imgW * this._scale) / 2;
    this._oy = (ch - this.imgH * this._scale) / 2;
  }

  _toImage(clientX, clientY) {
    const r = this.canvas.getBoundingClientRect();
    const x = (clientX - r.left - this._ox) / this._scale;
    const y = (clientY - r.top - this._oy) / this._scale;
    return [
      Math.max(0, Math.min(this.imgW, Math.round(x))),
      Math.max(0, Math.min(this.imgH, Math.round(y))),
    ];
  }

  _toCanvas([x, y]) {
    return [this._ox + x * this._scale, this._oy + y * this._scale];
  }

  // ── external state setters ────────────────────────────────────────────────
  setImage(img, width, height) {
    this.img = img;
    this.imgW = width;
    this.imgH = height;
    this.draft = [];
    this._fitAndDraw();
  }

  setObjects(objects) { this.objects = objects; this._draw(); }
  setClasses(colorMap) { this.classColors = colorMap; this._draw(); }
  setActiveClass(name) { this.activeClass = name; }

  // ── draft polygon interaction ─────────────────────────────────────────────
  _onClick(e) {
    if (!this.img || !this.activeClass) return;
    this.draft.push(this._toImage(e.clientX, e.clientY));
    this._draw();
  }

  undoDraftVertex() { this.draft.pop(); this._draw(); }
  cancelDraft() { this.draft = []; this._draw(); }

  closeDraft() {
    if (this.draft.length < 3 || !this.activeClass) { return false; }
    this.objects.push({ class: this.activeClass, polygon: this.draft });
    this.draft = [];
    this._draw();
    this.onObjectsChanged(this.objects);
    return true;
  }

  // ── rendering ─────────────────────────────────────────────────────────────
  _fitAndDraw() { this._fit(); this._draw(); }

  _color(name) { return this.classColors[name] || "#9aa0a6"; } // unknown class -> neutral

  _draw() {
    const { ctx } = this;
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    if (!this.img) return;
    ctx.drawImage(this.img, this._ox, this._oy, this.imgW * this._scale, this.imgH * this._scale);

    for (const obj of this.objects) this._drawPolygon(obj.polygon, this._color(obj.class), false);
    if (this.draft.length) this._drawPolygon(this.draft, this._color(this.activeClass), true);
  }

  _drawPolygon(polygon, color, isDraft) {
    const { ctx } = this;
    const pts = polygon.map((p) => this._toCanvas(p));
    ctx.beginPath();
    pts.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
    if (!isDraft) ctx.closePath();
    ctx.lineWidth = 2;
    ctx.strokeStyle = color;
    ctx.stroke();
    ctx.fillStyle = color + (isDraft ? "22" : "40"); // hex alpha
    ctx.fill();
    for (const [x, y] of pts) {
      ctx.beginPath();
      ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
    }
  }
}
