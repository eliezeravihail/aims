// Class panel: the editable list of labels (name + colour) and which one is
// currently "active" for drawing. Owns its own DOM inside a container element,
// persists edits through the api, and notifies the app when the active class
// or the colours change (so the canvas can repaint).

import { api } from "./api.js";

export class ClassPanel {
  constructor(container, { onChange } = {}) {
    this.container = container;
    this.onChange = onChange || (() => {});
    this.classes = [];       // [{name, color}]
    this.activeName = null;
  }

  async load() {
    const data = await api.getClasses();
    this.classes = data.classes;
    if (!this.activeName && this.classes.length) this.activeName = this.classes[0].name;
    this.render();
  }

  colorFor(label) {
    const c = this.classes.find((c) => c.name === label);
    return c ? c.color : "#888888";
  }

  activeLabel() {
    return this.activeName;
  }

  async _persist() {
    const saved = await api.saveClasses({ classes: this.classes });
    this.classes = saved.classes;
    if (!this.classes.find((c) => c.name === this.activeName)) {
      this.activeName = this.classes.length ? this.classes[0].name : null;
    }
    this.render();
    this.onChange();
  }

  _setActive(name) {
    this.activeName = name;
    this.render();
    this.onChange();
  }

  async _add() {
    const base = "class";
    let name = base;
    let n = 1;
    const names = new Set(this.classes.map((c) => c.name.toLowerCase()));
    while (names.has(name.toLowerCase())) name = `${base}${++n}`;
    this.classes.push({ name, color: randomColor() });
    this.activeName = name;
    await this._persist();
  }

  async _rename(oldName, newName) {
    newName = newName.trim();
    if (!newName || newName === oldName) return this.render();
    if (this.classes.some((c) => c.name.toLowerCase() === newName.toLowerCase())) {
      alert(`A class named "${newName}" already exists.`);
      return this.render();
    }
    const c = this.classes.find((c) => c.name === oldName);
    if (!c) return;
    c.name = newName;
    if (this.activeName === oldName) this.activeName = newName;
    await this._persist();
  }

  async _recolor(name, color) {
    const c = this.classes.find((c) => c.name === name);
    if (c) c.color = color;
    await this._persist();
  }

  async _delete(name) {
    if (!confirm(`Delete class "${name}"? Existing shapes keep the label.`)) return;
    this.classes = this.classes.filter((c) => c.name !== name);
    await this._persist();
  }

  render() {
    const el = this.container;
    el.innerHTML = "";

    const list = document.createElement("div");
    list.className = "class-list";

    for (const c of this.classes) {
      const row = document.createElement("div");
      row.className = "class-row" + (c.name === this.activeName ? " active" : "");

      const swatch = document.createElement("input");
      swatch.type = "color";
      swatch.value = c.color;
      swatch.title = "Change colour";
      swatch.className = "class-swatch";
      swatch.addEventListener("input", (e) => this._recolor(c.name, e.target.value));

      const name = document.createElement("input");
      name.type = "text";
      name.value = c.name;
      name.className = "class-name";
      name.addEventListener("change", (e) => this._rename(c.name, e.target.value));
      // Clicking the name selects it as the active class for drawing.
      name.addEventListener("focus", () => this._setActive(c.name));

      const del = document.createElement("button");
      del.textContent = "×";
      del.className = "class-del";
      del.title = "Delete class";
      del.addEventListener("click", () => this._delete(c.name));

      row.append(swatch, name, del);
      row.addEventListener("click", (e) => {
        if (e.target === name || e.target === swatch || e.target === del) return;
        this._setActive(c.name);
      });
      list.appendChild(row);
    }

    const add = document.createElement("button");
    add.textContent = "+ Add class";
    add.className = "class-add";
    add.addEventListener("click", () => this._add());

    el.append(list, add);
  }
}

function randomColor() {
  const palette = [
    "#e6194b", "#3cb44b", "#4363d8", "#f58231", "#911eb4",
    "#42d4f4", "#f032e6", "#bfef45", "#fabed4", "#469990",
  ];
  return palette[Math.floor(Math.random() * palette.length)];
}
