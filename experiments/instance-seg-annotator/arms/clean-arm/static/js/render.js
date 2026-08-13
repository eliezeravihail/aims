// Rendering: paint the image and all polygons onto the canvas for one frame.
//
// Pure drawing — reads Viewport + Editor state and a colour lookup, writes
// pixels. Holds no state of its own. Coordinates come from the editor in
// image space and are projected to screen space via the viewport.

const HANDLE_R = 4;        // vertex handle radius (css px)
const FIRST_PT_R = 6;      // draft start marker radius (css px)

export function render(viewport, image, editor, colorFor, cursor) {
  const ctx = viewport.ctx;
  const dpr = viewport.dpr;

  // Draw in CSS-pixel space regardless of device pixel ratio.
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, viewport.cssWidth, viewport.cssHeight);

  if (image && image.complete && image.naturalWidth) {
    const [ox, oy] = viewport.imageToScreen(0, 0);
    ctx.imageSmoothingEnabled = viewport.scale < 1;
    ctx.drawImage(
      image,
      ox,
      oy,
      viewport.imgW * viewport.scale,
      viewport.imgH * viewport.scale
    );
  }

  for (const obj of editor.objects) {
    drawPolygon(ctx, viewport, obj.points, colorFor(obj.label), obj.id === editor.selectedId);
  }
  const sel = editor.getSelected();
  if (sel) drawHandles(ctx, viewport, sel.points, colorFor(sel.label));

  if (editor.draft) drawDraft(ctx, viewport, editor.draft, colorFor(editor.draft.label), cursor);
}

function drawPolygon(ctx, vp, points, color, selected) {
  if (points.length < 2) return;
  ctx.beginPath();
  points.forEach((p, i) => {
    const [sx, sy] = vp.imageToScreen(p[0], p[1]);
    i === 0 ? ctx.moveTo(sx, sy) : ctx.lineTo(sx, sy);
  });
  ctx.closePath();
  ctx.fillStyle = withAlpha(color, selected ? 0.35 : 0.2);
  ctx.fill();
  ctx.lineWidth = selected ? 3 : 2;
  ctx.strokeStyle = color;
  ctx.stroke();
}

function drawHandles(ctx, vp, points, color) {
  for (const p of points) {
    const [sx, sy] = vp.imageToScreen(p[0], p[1]);
    ctx.beginPath();
    ctx.arc(sx, sy, HANDLE_R, 0, Math.PI * 2);
    ctx.fillStyle = "#fff";
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = color;
    ctx.stroke();
  }
}

function drawDraft(ctx, vp, draft, color, cursor) {
  const pts = draft.points;
  if (pts.length) {
    ctx.beginPath();
    pts.forEach((p, i) => {
      const [sx, sy] = vp.imageToScreen(p[0], p[1]);
      i === 0 ? ctx.moveTo(sx, sy) : ctx.lineTo(sx, sy);
    });
    // Rubber-band line to the cursor.
    if (cursor) ctx.lineTo(cursor[0], cursor[1]);
    ctx.lineWidth = 2;
    ctx.strokeStyle = color;
    ctx.setLineDash([5, 4]);
    ctx.stroke();
    ctx.setLineDash([]);

    // Vertices, with the first one enlarged (click it to close).
    pts.forEach((p, i) => {
      const [sx, sy] = vp.imageToScreen(p[0], p[1]);
      ctx.beginPath();
      ctx.arc(sx, sy, i === 0 ? FIRST_PT_R : HANDLE_R, 0, Math.PI * 2);
      ctx.fillStyle = i === 0 ? color : "#fff";
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = color;
      ctx.stroke();
    });
  }
}

// "#rrggbb" + alpha -> "rgba(...)".
function withAlpha(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
