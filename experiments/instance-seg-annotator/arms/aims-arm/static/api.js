// API client — the only place server URLs live. Everything else speaks in plain objects.

async function json(res) {
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail || detail; } catch (_) {}
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json();
}

export const api = {
  listImages: () => fetch("/api/images").then(json).then((d) => d.images),

  rawImageUrl: (id) => `/api/images/${encodeURIComponent(id)}/raw`,

  getAnnotations: (id) =>
    fetch(`/api/images/${encodeURIComponent(id)}/annotations`).then(json),

  putAnnotations: (id, objects) =>
    fetch(`/api/images/${encodeURIComponent(id)}/annotations`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ objects }),
    }).then(json),

  exportDataset: (options) =>
    fetch("/api/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(options),
    }).then(json),

  getClasses: () => fetch("/api/classes").then(json).then((d) => d.classes),

  putClasses: (classes) =>
    fetch("/api/classes", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ classes }),
    }).then(json).then((d) => d.classes),
};
