# Balash Guide State

## Mode

auto

## Loop cursor

ready-to-choose-next — tiled COCO export path delivered; awaiting next product change (none given).

## Current objective

**Kind:** implementation

**Objective:** Add a tiled-dataset export path for very large images: cut each image + its annotations
into configurable overlapping tiles, clip each object per tile it lands in, and write a standard
COCO instance-segmentation dataset — behind a new single-owner seam (`app/tiling.py` geometry +
`app/export.py` format), leaving the annotation model and the existing annotator untouched.

**Why now:** product owner's new requirement (large satellite imagery); the annotator must keep working
as before, so the export is confined to new modules plugged into existing seams.

**Exit criteria (all met):**
- [x] Large image cut into overlapping tiles; overlap configurable; full coverage (last tile clamped).
- [x] Object straddling a tile boundary clipped + remapped per tile; overlap → appears in >1 tile.
- [x] Object fully outside a tile absent from it.
- [x] Empty tiles exported validly (COCO image entry, no annotations).
- [x] Coordinate remap of a known point correct.
- [x] Export name path-safe (traversal/absolute/nested/dotfile → BadExportName/422).
- [x] Annotator still works as before; models.py unchanged; app boots under uvicorn.

**Superseded objective:** Build the annotator conforming to the agreed design (goals.md / architecture.md /
base-dependencies.md / decisions/0001): Workspace store; pydantic models owning validity; thin FastAPI
HTTP layer; Pillow-confined size probe; vanilla-JS/canvas frontend owning the display↔image transform.

**Why now (historical):** the design objective was met (docs filed, buildable); advanced to the slice so the
tool actually runs and round-trips annotations. That slice remains met (all its criteria still pass).

**Preserve:** substrate constraints; class-list-membership-not-a-validity-rule; authoritative dims;
full-image annotation and stored image-space coordinates (export must not touch them).

**Do not optimize for:** non-polygon shapes, nested folders, undo, multi-user; export formats beyond the
one standard COCO target; GC of orphan exports.

## Open Guide TODO

- (none open) — subtractive pass done (no dead code added; export reuses existing seams); companions
  filed + anchored for tiling/export/images/store/main/app; ADR 0002 recorded.

## Last evaluated result

export objective: **met** — 66/66 pytest pass (was 31; +35 for tiling/export/api). Every criterion
demonstrated: overlapping full-coverage tiling with clamp; straddler clipped+remapped per tile and
duplicated across overlap; outside-object absent; empty tiles export valid COCO; known-point remap
exact; export-name path safety (BadExportName/422). Live uvicorn boot serves UI + `POST /api/export`
writing images/ + annotations.json; bad overlap/name → 422. `models.py` and canvas.js untouched;
touched core modules additively (store `export_dir`, images `crop_to_file`, main route). New modules:
app/tiling.py, app/export.py. Records: ADR 0002, architecture/goals/dependencies updated, companions
anchored.
