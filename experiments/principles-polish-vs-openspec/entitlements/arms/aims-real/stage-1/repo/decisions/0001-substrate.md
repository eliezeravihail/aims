---
title: "Substrate: Python 3.11+, stdlib only"
date: 2026-09-23
---
Context: the substrate gate. The product owner fixed it in `substrate.md` (the "user set it" path), so it was
not asked again. Decision: Python 3.11+, standard library only, single process, no persistence. Consequence:
a new runtime dependency must be argued for in the design; none is expected at stage 1.
