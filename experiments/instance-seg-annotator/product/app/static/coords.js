// Image <-> viewport transform, JS side. The single frontend owner of zoom/pan
// math, mirroring app/coords.py exactly. No DOM, no fetch: pure functions so the
// canvas code can convert pointer input to image pixels before it ever becomes
// annotation geometry. Stored coordinates are always image-space; the transform
// only affects painting and pointer interpretation.
//
//   viewport = image * scale + (tx, ty)
//   image    = (viewport - (tx, ty)) / scale

export function makeTransform(scale = 1, tx = 0, ty = 0) {
  if (scale <= 0) throw new Error("scale must be positive");
  return { scale, tx, ty };
}

export function imageToViewport([x, y], t) {
  return [x * t.scale + t.tx, y * t.scale + t.ty];
}

export function viewportToImage([x, y], t) {
  return [(x - t.tx) / t.scale, (y - t.ty) / t.scale];
}

export function zoomed(t, factor, [cx, cy]) {
  const scale = t.scale * factor;
  const tx = cx - (cx - t.tx) * factor;
  const ty = cy - (cy - t.ty) * factor;
  return { scale, tx, ty };
}

export function panned(t, dx, dy) {
  return { scale: t.scale, tx: t.tx + dx, ty: t.ty + dy };
}

// Fit an (imgW x imgH) image centered inside a (viewW x viewH) viewport.
export function fitTransform(imgW, imgH, viewW, viewH, padding = 20) {
  const sx = (viewW - 2 * padding) / imgW;
  const sy = (viewH - 2 * padding) / imgH;
  const scale = Math.max(1e-6, Math.min(sx, sy));
  const tx = (viewW - imgW * scale) / 2;
  const ty = (viewH - imgH * scale) / 2;
  return { scale, tx, ty };
}
