---
title: "goals"
date: 2026-08-13
---

## Primary goal
A local, single-user web tool for **multi-class instance segmentation** annotation, run from a
container. Load an image, draw one or more **polygon instances**, assign each a **class** from a
configurable class list, and save the annotations to disk.

## Use scenarios
- Point the tool at a folder of images; step through them; for each, draw polygon instances, label
  each with a class, save; move to the next.
- Later, export the annotated set as a training dataset.

## Non-goals (stage 1)
- No multi-user / auth / collaboration.
- No automatic/AI-assisted segmentation — manual polygons only.
- No cloud storage — local disk, inside the container's mounted volume.

## Grounded product decisions (day-zero)
- Annotation primitive: a **polygon** (ordered vertices) per instance; each instance has a class label.
  (Instance segmentation = per-instance masks; polygons are the editable representation.)
- Classes: a configurable list (name + color), fixed per project.
- Persistence: annotations stored per source image as JSON on disk (a mounted volume).
- Runs locally from a container; the browser talks to a local backend.
