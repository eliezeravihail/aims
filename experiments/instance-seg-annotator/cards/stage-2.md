# Stage 2 — the new requirement

The tool is working well. New situation:

The images I now need to annotate are **very large satellite images** — far too big to annotate or to
feed a training pipeline as a single image.

I need the tool to:

- Take a large source image (and its annotations) and **cut it into smaller tiles** that **overlap** each
  other by a configurable amount, so objects near a tile's edge aren't lost.
- **Export a folder** that holds a **training dataset**: the tile images together with their annotations,
  in a **standard format that a segmentation-model training pipeline can consume**.
- An object that sits across a tile boundary should be handled sensibly for each tile it appears in.

Build it well, same as before. Ask me one product question at a time if something is genuinely ambiguous.
When it works, say so and how to run the tiling/export.
</content>
