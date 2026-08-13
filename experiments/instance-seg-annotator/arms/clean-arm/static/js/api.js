// Thin wrappers over the backend HTTP API. No UI logic here — just fetch.

async function _json(res) {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body && body.detail) detail = JSON.stringify(body.detail);
    } catch (_) { /* non-JSON error body */ }
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json();
}

export const api = {
  // -> [{name, width, height, object_count}, ...]
  listImages() {
    return fetch("/api/images").then(_json);
  },

  imageFileUrl(name) {
    return `/api/images/${encodeURIComponent(name)}/file`;
  },

  // URL that downloads the whole folder as a zipped COCO dataset of
  // overlapping tiles. tileSize / overlap are in original-image pixels.
  exportUrl(tileSize, overlap) {
    const q = new URLSearchParams({ tile_size: tileSize, overlap });
    return `/api/export?${q.toString()}`;
  },

  // -> {image, width, height, objects: [{id, label, points}]}
  getAnnotation(name) {
    return fetch(`/api/images/${encodeURIComponent(name)}/annotation`).then(_json);
  },

  saveAnnotation(name, annotation) {
    return fetch(`/api/images/${encodeURIComponent(name)}/annotation`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(annotation),
    }).then(_json);
  },

  // -> {classes: [{name, color}]}
  getClasses() {
    return fetch("/api/classes").then(_json);
  },

  saveClasses(classList) {
    return fetch("/api/classes", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(classList),
    }).then(_json);
  },
};
