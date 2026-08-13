# Experiment — building a real product with aims (instance-segmentation annotator)

A real, evolving-task experiment: **aims builds a working, containerized product**, and files its design
knowledge as co-located records (companions beside code + root `goals.md`/`architecture.md`/`decisions/`),
so the structure itself carries the design.

- **Stage 1 (general first requirement):** a local, container-run web app for **multi-class instance
  segmentation** annotation — load an image, draw polygon instances, assign a class, save.
- **Stage 2 (evolution):** large **satellite images** arrive → cut into **overlapping tiles**, and
  export a folder holding a **training dataset in a standard instance-seg format**.

The design axis under stress across the evolution: the seam between *annotation geometry* and *how
images are presented/stored* — Stage 2 (tiling + coordinate remap + clipping instances to tile borders)
is exactly what a good boundary must absorb without a tear-open.

Method: I act as the Guide (discovery → one design objective at a time → delegate to a Worker → measure
→ file records). The product lives in this directory as its own root; `results.md` records how the
evolution landed.
