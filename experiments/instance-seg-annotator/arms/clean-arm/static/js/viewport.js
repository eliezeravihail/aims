// Viewport: the mapping between image-pixel space and on-screen canvas space.
//
// All annotation coordinates live in image-pixel space (see models.py). The
// viewport owns the current scale + translation used to show the image, plus
// the two conversions the rest of the app needs:
//   imageToScreen(x, y)  screenToImage(x, y)
// It also keeps the canvas backing store sized correctly for the display
// (handling high-DPI screens) so drawing stays crisp.

export class Viewport {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.scale = 1;      // image px -> css px
    this.tx = 0;         // css-px translation
    this.ty = 0;
    this.imgW = 1;
    this.imgH = 1;
    this.dpr = window.devicePixelRatio || 1;
  }

  // Match the canvas backing store to its displayed size (call on resize).
  syncSize() {
    const rect = this.canvas.getBoundingClientRect();
    this.dpr = window.devicePixelRatio || 1;
    this.canvas.width = Math.max(1, Math.round(rect.width * this.dpr));
    this.canvas.height = Math.max(1, Math.round(rect.height * this.dpr));
  }

  get cssWidth() {
    return this.canvas.width / this.dpr;
  }
  get cssHeight() {
    return this.canvas.height / this.dpr;
  }

  // Fit the whole image inside the canvas and centre it.
  fit(imgW, imgH) {
    this.imgW = imgW;
    this.imgH = imgH;
    const cw = this.cssWidth;
    const ch = this.cssHeight;
    const s = Math.min(cw / imgW, ch / imgH);
    this.scale = s;
    this.tx = (cw - imgW * s) / 2;
    this.ty = (ch - imgH * s) / 2;
  }

  imageToScreen(x, y) {
    return [x * this.scale + this.tx, y * this.scale + this.ty];
  }

  screenToImage(sx, sy) {
    return [(sx - this.tx) / this.scale, (sy - this.ty) / this.scale];
  }

  // Zoom by `factor` keeping the point under (sx, sy) fixed on screen.
  zoomAt(sx, sy, factor) {
    const [ix, iy] = this.screenToImage(sx, sy);
    this.scale = clamp(this.scale * factor, 0.05, 40);
    this.tx = sx - ix * this.scale;
    this.ty = sy - iy * this.scale;
  }

  panBy(dx, dy) {
    this.tx += dx;
    this.ty += dy;
  }
}

function clamp(v, lo, hi) {
  return Math.max(lo, Math.min(hi, v));
}
